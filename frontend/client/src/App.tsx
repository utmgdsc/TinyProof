import { useEffect, useRef, useState } from "react";
import Split from "react-split";
import * as monaco from "monaco-editor";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { LeanMonaco, LeanMonacoEditor, LeanMonacoOptions } from "lean4monaco";
import LZString from "lz-string";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCode } from "@fortawesome/free-solid-svg-icons";

// Local imports
import LeanLogo from "./assets/logo.svg";
import defaultSettings, {
  IPreferencesContext,
  lightThemes,
} from "./config/settings";
import { Menu } from "./Navigation";
import { PreferencesContext } from "./Popups/Settings";
import {
  fixedEncodeURIComponent,
  formatArgs,
  lookupUrl,
  parseArgs,
} from "./utils/UrlParsing";
import { useWindowDimensions } from "./utils/WindowWidth";

// CSS
import "./css/App.css";
import "./css/Editor.css";
import useSolver from "./hooks/useSolver";

/** Returns true if the browser wants dark mode */
function isBrowserDefaultDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function App() {
  const editorRef = useRef<HTMLDivElement>(null);
  const infoviewRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<boolean | null>(false);
  const [editor, setEditor] = useState<monaco.editor.IStandaloneCodeEditor>();
  const [leanMonaco, setLeanMonaco] = useState<LeanMonaco>();
  const [loaded, setLoaded] = useState<boolean>(false);
  const [preferences, setPreferences] =
    useState<IPreferencesContext>(defaultSettings);
  const { width } = useWindowDimensions();

  const [proofs, setProofs] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const [exploreMode, setExploreMode] = useState(false);

  // const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  // const socket = new WebSocket(`${protocol}://${window.location.host}/ws`)
  const socketRef = useRef<WebSocket | null>(null);

  const goLeft = () => {
    if (proofs.length === 0) return;
    const newIndex = currentIndex === 0 ? proofs.length - 1 : currentIndex - 1;
    setCurrentIndex(newIndex);
    setContent(proofs[newIndex]);
  };

  const goRight = () => {
    if (proofs.length === 0) return;
    const newIndex = currentIndex === proofs.length - 1 ? 0 : currentIndex + 1;
    setCurrentIndex(newIndex);
    setContent(proofs[newIndex]);
  };

  const toggleExploreMode = () => {
    setExploreMode((prev) => !prev);
  };

  // Lean4monaco options
  const [options, setOptions] = useState<LeanMonacoOptions>({
    // placeholder, updated below
    websocket: { url: "" },
  });

  // Because of Monaco's missing mobile support we add a codeMirror editor
  // which can be enabled to do editing.
  // TODO: It would be nice to integrate Lean into CodeMirror better.
  // first step could be to pass the cursor selection to the underlying monaco editor
  const [codeMirror, setCodeMirror] = useState(false);

  // the user data
  const [code, setCode] = useState<string>("");
  const [project, setProject] = useState<string>("mathlib-demo");
  const [url, setUrl] = useState<string | null>(null);
  const [codeFromUrl, setCodeFromUrl] = useState<string>("");

  /** Monaco editor requires the code to be set manually. */
  function setContent(code: string) {
    const model = editor?.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, "lean4");
      model.setValue(code);
    } else {
      console.warn("Editor model is not ready yet.");
    }
    setCode(code);
  }

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socketRef.current = new WebSocket(
      `${protocol}://${window.location.host}/ws`
    );

    socketRef.current.onopen = () => {
      console.log("[WebSocket] Connected");
    };

    socketRef.current.onmessage = (event) => {
      const proofAttempt = event.data;
      setContent(proofAttempt);
    };

    socketRef.current.onclose = () => {
      console.log("[WebSocket] Disconnected");
    };

    return () => {
      socketRef.current?.close();
    };
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(code);
        console.log("[WebSocket] Sent code:", code);
      }
    }, 500); // waits 500ms after last change

    return () => clearTimeout(timeout);
  }, [code]);

  useEffect(() => {
    // MOCK PROOFS
    fetch("http://localhost:5050/proofs")
      .then((res) => res.json())
      .then((data) => {
        setProofs(data.proofs);
        // setContent(data.proofs[0])  COMMENTED OUT FOR TESTING SYNTAX HIGHLIGHTING
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (editor && proofs.length > 0) {
      setContent(proofs[currentIndex]);
    }
  }, [editor, proofs]);

  // Load preferences from store in the beginning
  useEffect(() => {
    console.debug("[Lean4web] Preferences: Loading.");

    // only load them once
    if (loaded) {
      return;
    }

    let saveInLocalStore = false;
    let newPreferences: any = { ...preferences }; // TODO: need `any` instead of `IPreferencesContext` here to satisfy ts
    for (const [key, value] of Object.entries(preferences)) {
      let storedValue = window.localStorage.getItem(key);
      if (storedValue) {
        saveInLocalStore = true;
        console.debug(
          `[Lean4web] Found stored value for ${key}: ${storedValue}`
        );
        if (typeof value === "string") {
          newPreferences[key] = storedValue;
        } else if (typeof value === "boolean") {
          // Boolean values
          newPreferences[key] = storedValue === "true";
        } else {
          // other values aren't implemented yet.
          console.error(
            `[Lean4web] Preferences (key: ${key}) contain a value of unsupported type: ${typeof value}`
          );
        }
      } else {
        // no stored preferences, set a default value
        if (key == "theme") {
          if (isBrowserDefaultDark()) {
            console.debug("[Lean4web] Preferences: Set dark theme.");
            newPreferences["theme"] = "Visual Studio Dark";
          } else {
            console.debug("[Lean4web] Preferences: Set light theme.");
            newPreferences["theme"] = "Visual Studio Light";
          }
        }
      }
    }
    newPreferences["saveInLocalStore"] = saveInLocalStore;
    setPreferences(newPreferences);
    setLoaded(true);
  }, []);

  // Use the window width to switch between mobile/desktop layout
  useEffect(() => {
    // Wait for preferences to be loaded
    if (!loaded) {
      return;
    }

    const _mobile = width < 800;
    if (!preferences.saveInLocalStore && _mobile !== preferences.mobile) {
      setPreferences({ ...preferences, mobile: _mobile });
    }
  }, [width, loaded]);

  useEffect(() => {
    const handleResize = () => {
      editor?.layout();
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [editor]);

  useEffect(() => {
    // ATTEMPTED TO FIX GREEN BAR
    if (exploreMode) {
      console.log(
        "[Lean4web] Explore mode enabled: skipping LeanMonaco startup."
      );
      return; // Don't set options or start LeanMonaco when in explore mode
    }

    const socketUrl =
      (window.location.protocol === "https:" ? "wss://" : "ws://") +
      window.location.host +
      "/websocket/" +
      project;
    console.log(`[Lean4web] socket url: ${socketUrl}`);

    const _options: LeanMonacoOptions = {
      websocket: { url: socketUrl },
      htmlElement: editorRef.current ?? undefined,
      vscode: {
        "workbench.colorTheme": preferences.theme,
        "editor.tabSize": 2,
        "editor.lightbulb.enabled": "on",
        "editor.wordWrap": preferences.wordWrap ? "on" : "off",
        "editor.wrappingStrategy": "advanced",
        "editor.semanticHighlighting.enabled": true,
        "editor.acceptSuggestionOnEnter": preferences.acceptSuggestionOnEnter
          ? "on"
          : "off",
        "lean4.input.eagerReplacementEnabled": true,
        "lean4.input.leader": preferences.abbreviationCharacter,
      },
    };

    setOptions(_options);
  }, [editorRef, project, preferences, exploreMode]);

  // Setting up the editor and infoview
  useEffect(() => {
    // Wait for preferences to be loaded
    if (!loaded) {
      return;
    }
    console.debug("[Lean4web] Restarting Editor!");
    var _leanMonaco = new LeanMonaco();
    var leanMonacoEditor = new LeanMonacoEditor();

    if (!exploreMode) {
      _leanMonaco.setInfoviewElement(infoviewRef.current!);
    } else {
      const dummy = document.createElement("div");
      dummy.style.display = "none";
      _leanMonaco.setInfoviewElement(dummy);
    }
    (async () => {
      await _leanMonaco.start(options);
      await leanMonacoEditor.start(
        editorRef.current!,
        `/project/${project}.lean`,
        code
      );

      setEditor(leanMonacoEditor.editor);
      setLeanMonaco(_leanMonaco);

      const model = leanMonacoEditor.editor.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, "lean4");
      }

      console.log("Language is:", model?.getLanguageId());

      useEffect(() => {
        if (!editorRef.current || !editor) return;

        const observer = new ResizeObserver(() => {
          editor.layout();
        });

        observer.observe(editorRef.current);

        return () => observer.disconnect();
      }, [editor]);

      // Add a `Paste` option to the context menu on mobile.
      // Monaco does not support clipboard pasting as all browsers block it
      // due to security reasons. Therefore we use a codeMirror editor overlay
      // which features good mobile support (but no Lean support yet)
      if (preferences.mobile) {
        leanMonacoEditor.editor?.addAction({
          id: "myPaste",
          label: "Paste: open 'Plain Editor' for editing on mobile",
          // keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_V],
          contextMenuGroupId: "9_cutcopypaste",
          run: (_editor) => {
            setCodeMirror(true);
          },
        });
      }

      // // TODO: This was an approach to create a new definition provider, but it
      // // wasn't that useful. I'll leave it here in connection with the TODO below for
      // // reference.
      // monaco.languages.registerDefinitionProvider('lean4', {
      //   provideDefinition(model, position) {
      //     const word = model.getWordAtPosition(position);
      //     if (word) {
      //       console.log(`[Lean4web] Providing definition for: ${word.word}`);
      //       // Return the location of the definition
      //       return [
      //         {
      //           uri: model.uri,
      //           range: {startLineNumber: 0, startColumn: word.startColumn, endColumn: word.endColumn, endLineNumber: 0}, // Replace with actual definition range
      //         },
      //       ];
      //     }
      //     return null;
      //   },
      // });

      // TODO: Implement Go-To-Definition better
      // This approach only gives us the file on the server (plus line number) it wants
      // to open, is there a better approach?
      const editorService = (leanMonacoEditor.editor as any)
        ?._codeEditorService;
      if (editorService) {
        const openEditorBase = editorService.openCodeEditor.bind(editorService);
        editorService.openCodeEditor = async (input: any, source: any) => {
          const result = await openEditorBase(input, source);
          if (result === null) {
            // found this out with `console.debug(input)`:
            // `resource.path` is the file go-to-def tries to open on the disk
            // we try to create a doc-gen link from that. Could not extract the
            // (fully-qualified) decalaration name... with that one could
            // call `...${path}.html#${declaration}`
            let path = input.resource.path
              .replace(new RegExp("^.*/(?:lean|.lake/packages/[^/]+/)"), "")
              .replace(new RegExp(".lean$"), "");

            if (
              window.confirm(
                `Do you want to open the docs?\n\n${path} (line ${input.options.selection.startLineNumber})`
              )
            ) {
              let newTab = window.open(
                `https://leanprover-community.github.io/mathlib4_docs/${path}.html`,
                "_blank"
              );
              if (newTab) {
                newTab.focus();
              }
            }
          }
          return null;
          // return result // always return the base result
        };
      }

      // Keeping the `code` state up-to-date with the changes in the editor
      leanMonacoEditor.editor?.onDidChangeModelContent(() => {
        setCode(leanMonacoEditor.editor?.getModel()?.getValue()!);
        console.log(editor?.getModel()?.getLanguageId());
      });
    })();
    return () => {
      leanMonacoEditor.dispose();
      _leanMonaco.dispose();
    };
  }, [
    loaded,
    project,
    preferences,
    options,
    infoviewRef,
    editorRef,
    exploreMode,
  ]);

  // Read the URL arguments once
  useEffect(() => {
    if (!editor) {
      return;
    }
    console.debug("[Lean4web] editor is ready");

    // Parse args
    let args = parseArgs();
    if (args.code) {
      let _code = decodeURIComponent(args.code);
      setContent(_code);
    } else if (args.codez) {
      let _code = LZString.decompressFromBase64(args.codez);
      setContent(_code);
    }

    if (args.url) {
      setUrl(lookupUrl(decodeURIComponent(args.url)));
    }
    if (args.project && args.project != project) {
      console.log(`[Lean4web] setting project to ${args.project}`);
      setProject(args.project);
    }
  }, [editor]);

  // Load content from source URL.
  // Once the editor, this reads the content of any provided `url=` in the URL and
  // saves this content as `contentFromURL`. It is important that we only do this once
  // the editor is loaded, as the `useEffect` below only triggers when the `contentFromURL`
  // changes, otherwise it might overwrite local changes too often.
  useEffect(() => {
    if (!editor || !url) {
      return;
    }
    console.debug(`[Lean4web] Loading from ${url}`);
    fetch(url)
      .then((response) => response.text())
      .then((code) => {
        setCodeFromUrl(code);
      })
      .catch((err) => {
        let errorTxt = `ERROR: ${err.toString()}`;
        console.error(errorTxt);
        setCodeFromUrl(errorTxt);
      });
  }, [url, editor]);

  // Sets the editors content to the content from the loaded URL.
  // As described above, this requires the editor is loaded, but we do not want to
  // trigger this effect every time the editor is reloaded (e.g. config change) as otherwise
  // we would constantly overwrite the user's local changes
  useEffect(() => {
    if (!codeFromUrl) {
      return;
    }
    setContent(codeFromUrl);
  }, [codeFromUrl]);

  // Keep the URL updated on change
  useEffect(() => {
    if (!editor) {
      return;
    }

    let _project = project == "mathlib-demo" ? null : project;
    let args: {
      project: string | null;
      url: string | null;
      code: string | null;
      codez: string | null;
    };
    if (code === "") {
      args = {
        project: _project,
        url: null,
        code: null,
        codez: null,
      };
    } else if (url != null && code == codeFromUrl) {
      args = {
        project: _project,
        url: encodeURIComponent(url),
        code: null,
        codez: null,
      };
    } else if (preferences.compress) {
      // LZ padds the string with trailing `=`, which mess up the argument parsing
      // and aren't needed for LZ encoding, so we remove them.
      const compressed = LZString.compressToBase64(code).replace(/=*$/, "");
      // // Note: probably temporary; might be worth to always compress as with whitespace encoding
      // // it needs very little for the compressed version to be shorter
      // const encodedCode = fixedEncodeURIComponent(code)
      // console.debug(`[Lean4web]: code length: ${encodedCode.length}, compressed: ${compressed.length}`)
      // if (compressed.length < encodedCode.length) {
      args = {
        project: _project,
        url: null,
        code: null,
        codez: compressed,
      };
      // } else {
      //   args = {
      //     project: _project,
      //     url: null,
      //     code: encodedCode,
      //     codez: null
      //   }
      // }
    } else {
      args = {
        project: _project,
        url: null,
        code: fixedEncodeURIComponent(code),
        codez: null,
      };
    }
    history.replaceState(undefined, undefined!, formatArgs(args));
  }, [editor, project, code, codeFromUrl]);

  const { start, generating, currentStep } = useSolver({
    url: "http://localhost:5050/ws",
    onConnect: () => {
      console.log("Connected to solver");
      setContent("Generating proof...");
    },
    onDisconnect: () => {
      console.log("Disconnected from solver");
    },
    onError: (error) => {
      console.error("Solver error:", error);
    },
    onProofStep: (step) => {
      setContent(step);
    },
  });

  return (
    <PreferencesContext.Provider value={{ preferences, setPreferences }}>
      <div
        className="app monaco-editor"
        style={{ display: "flex", flexDirection: "column", height: "100vh" }}
      >
        <nav>
          <LeanLogo />

          {/* Dark/light theme toggle */}
          <button
            onClick={() => {
              const newTheme =
                preferences.theme === "Visual Studio Dark"
                  ? "Visual Studio Light"
                  : "Visual Studio Dark";
              setPreferences({ ...preferences, theme: newTheme });
              localStorage.setItem("theme", newTheme); // Persist it

              setTimeout(() => {
                leanMonaco?.restart?.();
              }, 100);
            }}
            style={{
              marginLeft: "1rem",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#333",
              color: "#fff",
              fontWeight: "bold",
              cursor: generating ? "not-allowed" : "pointer",
              boxShadow: "0 2px 6px rgba(0, 0, 0, 0.15)",
              opacity: generating ? 0.6 : 1,
            }}
          >
            Toggle Theme
          </button>

          <Menu
            code={code}
            setContent={setContent}
            project={project}
            setProject={setProject}
            setUrl={setUrl}
            codeFromUrl={codeFromUrl}
            restart={leanMonaco?.restart}
            codeMirror={codeMirror}
            setCodeMirror={setCodeMirror}
          />
        </nav>
        <div style={{ flex: 1 }}>
          <Split
            className={`editor ${dragging ? "dragging" : ""}`}
            gutter={(_index, _direction) => {
              const gutter = document.createElement("div");
              gutter.className = `gutter`; // no `gutter-${direction}` as it might change
              return gutter;
            }}
            gutterStyle={(_dimension, gutterSize, _index) => {
              return {
                width: preferences.mobile ? "100%" : `${gutterSize}px`,
                height: preferences.mobile ? `${gutterSize}px` : "100%",
                cursor: preferences.mobile ? "row-resize" : "col-resize",
                "margin-left": preferences.mobile ? 0 : `-${gutterSize}px`,
                "margin-top": preferences.mobile ? `-${gutterSize}px` : 0,
                "z-index": 0,
              };
            }}
            gutterSize={5}
            onDragStart={() => setDragging(true)}
            onDragEnd={() => setDragging(false)}
            sizes={preferences.mobile ? [50, 50] : [70, 30]}
            direction={preferences.mobile ? "vertical" : "horizontal"}
            style={{
              flexDirection: preferences.mobile ? "column" : "row",
              height: "100%",
            }}
          >
            <div
              className="codeview-wrapper"
              style={
                preferences.mobile ? { width: "100%" } : { height: "100%" }
              }
            >
              {codeMirror && (
                <CodeMirror
                  className="codeview plain"
                  value={code}
                  extensions={[EditorView.lineWrapping]}
                  height="100%"
                  maxHeight="100%"
                  theme={
                    lightThemes.includes(preferences.theme) ? "light" : "dark"
                  }
                  onChange={setContent}
                />
              )}
              <div
                ref={editorRef}
                className={`codeview${codeMirror ? " hidden" : ""}`}
                style={{
                  flex: 1,
                  width: "100%",
                  overflow: "hidden",
                  minHeight: 0,
                }}
              />
            </div>
            <div
              ref={infoviewRef}
              className={`${
                lightThemes.includes(preferences.theme)
                  ? "vscode-light"
                  : "vscode-dark"
              } infoview`}
              style={{
                display: exploreMode ? "none" : undefined,
                ...(preferences.mobile
                  ? { width: "100%" }
                  : { height: "100%" }),
              }}
            >
              <p
                className={`editor-support-warning${
                  codeMirror ? "" : " hidden"
                }`}
              >
                You are in the plain text editor
                <br />
                <br />
                Go back to the Monaco Editor (click{" "}
                <FontAwesomeIcon icon={faCode} />) for the infoview to update!
              </p>
            </div>
          </Split>
        </div>

        {/* Fixed bottom button bar */}
        <div
          style={{
            padding: "0.75rem",
            display: "flex",
            justifyContent: "center",
            gap: "1rem",
            borderTop: "1px solid #ddd",
            background: "#f9f9f9",
          }}
        >
          <button
            onClick={goLeft}
            disabled={generating}
            style={{
              fontSize: "1.5rem",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#e0e0e0",
              cursor: generating ? "not-allowed" : "pointer",
              boxShadow: "0 2px 6px rgba(0, 0, 0, 0.1)",
              opacity: generating ? 0.6 : 1,
            }}
          >
            ⬅️
          </button>
          <button
            onClick={goRight}
            disabled={generating}
            style={{
              fontSize: "1.5rem",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#e0e0e0",
              cursor: generating ? "not-allowed" : "pointer",
              boxShadow: "0 2px 6px rgba(0, 0, 0, 0.1)",
              opacity: generating ? 0.6 : 1,
            }}
          >
            ➡️
          </button>
          <button
            onClick={toggleExploreMode}
            disabled={generating}
            style={{
              marginLeft: "auto",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: exploreMode ? "#f0c040" : "#4caf50",
              color: "white",
              fontWeight: "bold",
              cursor: generating ? "not-allowed" : "pointer",
              boxShadow: "0 2px 6px rgba(0, 0, 0, 0.15)",
              opacity: generating ? 0.6 : 1,
            }}
          >
            {exploreMode ? "Exit Explore Mode" : "Enter Explore Mode"}
          </button>
          <button
            onClick={start}
            disabled={generating}
            style={{
              marginLeft: "1rem",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#2196f3",
              color: "white",
              fontWeight: "bold",
              cursor: generating ? "not-allowed" : "pointer",
              boxShadow: "0 2px 6px rgba(0, 0, 0, 0.15)",
              opacity: generating ? 0.6 : 1,
            }}
          >
            {generating ? `In Step ${currentStep}` : "Start Proof Solver"}
          </button>
        </div>
      </div>
    </PreferencesContext.Provider>
  );
}

export default App;
