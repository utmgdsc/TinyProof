import {
  ChangeEvent,
  Dispatch,
  FC,
  MouseEventHandler,
  ReactNode,
  SetStateAction,
  useContext,
  useState,
} from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  IconDefinition,
  faArrowRotateRight,
  faCode,
  faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";
import {
  faArrowUpRightFromSquare,
  faBars,
  faXmark,
  faShield,
  faHammer,
  faGear,
} from "@fortawesome/free-solid-svg-icons";

import SettingsPopup, { PreferencesContext } from "./Popups/Settings";
import PrivacyPopup from "./Popups/PrivacyPolicy";
import ImpressumPopup from "./Popups/Impressum";
import ToolsPopup from "./Popups/Tools";
import LoadUrlPopup from "./Popups/LoadUrl";
import LoadZulipPopup from "./Popups/LoadZulip";

import lean4webConfig from "./config/config";
import "./css/Modal.css";
import "./css/Navigation.css";
import { lookupUrl } from "./utils/UrlParsing";

/** A button to appear in the hamburger menu or to navigation bar. */
export const NavButton: FC<{
  icon?: IconDefinition;
  iconElement?: JSX.Element;
  text: string;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
  href?: string;
}> = ({ icon, iconElement, text, onClick = () => {}, href = null }) => {
  // note: it seems that we can just leave the `target="_blank"` and it has no
  // effect on links without a `href`. If not, add `if (href)` statement here...
  return (
    <a className="nav-link" onClick={onClick} href={href!} target="_blank">
      {iconElement ?? <FontAwesomeIcon icon={icon!} />}&nbsp;{text}
    </a>
  );
};

/** A button to appear in the hamburger menu or to navigation bar. */
export const Dropdown: FC<{
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  icon?: IconDefinition;
  text?: string;
  useOverlay?: boolean;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
  children?: ReactNode;
}> = ({ open, setOpen, icon, text, useOverlay = false, onClick, children }) => {
  return (
    <>
      <div className="dropdown">
        <NavButton
          icon={icon}
          text={text!}
          onClick={(ev) => {
            setOpen(!open);
            onClick!(ev);
            ev.stopPropagation();
          }}
        />
        {open && (
          <div
            className={`dropdown-content${open ? "" : " "}`}
            onClick={() => setOpen(false)}
          >
            {children}
          </div>
        )}
      </div>
      {useOverlay && open && (
        <div
          className="dropdown-overlay"
          onClick={(ev) => {
            setOpen(false);
            ev.stopPropagation();
          }}
        />
      )}
    </>
  );
};

/** A popup which overlays the entire screen. */
export const Popup: FC<{
  open: boolean;
  handleClose: () => void; // TODO: what's the correct type?
  children?: ReactNode;
}> = ({ open, handleClose, children }) => {
  return (
    <div className={`modal-wrapper${open ? "" : " hidden"}`}>
      <div className="modal-backdrop" onClick={handleClose} />
      <div className="modal">
        <div
          className="codicon codicon-close modal-close"
          onClick={handleClose}
        ></div>
        {children}
      </div>
    </div>
  );
};

/** The Navigation menu */
export const Menu: FC<{
  code: string;
  setContent: (code: string) => void;
  project: string;
  setProject: Dispatch<SetStateAction<string>>;
  setUrl: Dispatch<SetStateAction<string | null>>;
  codeFromUrl: string;
  restart?: () => void;
  codeMirror: boolean;
  setCodeMirror: Dispatch<SetStateAction<boolean>>;
}> = ({
  code,
  setContent,
  project,
  setProject,
  setUrl,
  codeFromUrl,
  restart,
  codeMirror,
  setCodeMirror,
}) => {
  // state for handling the dropdown menus
  const [openNav, setOpenNav] = useState(false);
  const [openExample, setOpenExample] = useState(false);
  const [openLoad, setOpenLoad] = useState(false);
  const [loadUrlOpen, setLoadUrlOpen] = useState(false);
  const [loadZulipOpen, setLoadZulipOpen] = useState(false);

  // state for the popups
  const [impressumOpen, setImpressumOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { preferences } = useContext(PreferencesContext);

  const loadFromUrl = (
    url: string,
    project: string | undefined = undefined
  ) => {
    url = lookupUrl(url);
    console.debug("load code from url");
    setUrl((oldUrl: string | null) => {
      if (oldUrl === url) {
        setContent(codeFromUrl);
      }
      return url;
    });
    if (project) {
      setProject(project);
    }
  };

  const hasImpressum =
    lean4webConfig.impressum || lean4webConfig.contactDetails;

  return (
    <div className="menu">
      <select
        name="leanVersion"
        value={project}
        onChange={(ev) => {
          setProject(ev.target.value);
          console.log(`set Lean project to: ${ev.target.value}`);
        }}
      >
        {lean4webConfig.projects.map((proj) => (
          <option key={proj.folder} value={proj.folder}>
            {proj.name ?? proj.folder}
          </option>
        ))}
      </select>
      {preferences.mobile && (
        <NavButton
          icon={faCode}
          text={codeMirror ? "Lean" : "Text"}
          onClick={() => {
            setCodeMirror(!codeMirror);
          }}
        />
      )}
      <Dropdown
        open={openNav}
        setOpen={setOpenNav}
        icon={openNav ? faXmark : faBars}
        onClick={() => {
          setOpenExample(false);
          setOpenLoad(false);
        }}
      >
        <NavButton
          icon={faGear}
          text="Settings"
          onClick={() => {
            setSettingsOpen(true);
          }}
        />
        <NavButton
          icon={faHammer}
          text="Lean Info"
          onClick={() => setToolsOpen(true)}
        />
        <NavButton
          icon={faArrowRotateRight}
          text="Restart server"
          onClick={restart}
        />
        {hasImpressum && (
          <NavButton
            icon={faInfoCircle}
            text={"Impressum"}
            onClick={() => {
              setImpressumOpen(true);
            }}
          />
        )}
        <NavButton
          icon={faArrowUpRightFromSquare}
          text="Lean community"
          href="https://leanprover-community.github.io/"
        />
        <NavButton
          icon={faArrowUpRightFromSquare}
          text="Lean documentation"
          href="https://leanprover.github.io/lean4/doc/"
        />
      </Dropdown>
      {hasImpressum && (
        <ImpressumPopup
          open={impressumOpen}
          handleClose={() => setImpressumOpen(false)}
        />
      )}
      <ToolsPopup
        open={toolsOpen}
        handleClose={() => setToolsOpen(false)}
        project={project}
      />
      <SettingsPopup
        open={settingsOpen}
        handleClose={() => setSettingsOpen(false)}
        closeNav={() => setOpenNav(false)}
        project={project}
        setProject={setProject}
      />
      <LoadUrlPopup
        open={loadUrlOpen}
        handleClose={() => setLoadUrlOpen(false)}
        loadFromUrl={loadFromUrl}
      />
      <LoadZulipPopup
        open={loadZulipOpen}
        handleClose={() => setLoadZulipOpen(false)}
        setContent={setContent}
      />
    </div>
  );
};
