import {
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
} from "@fortawesome/free-solid-svg-icons";
import {
  faArrowUpRightFromSquare,
  faBars,
  faXmark,
  faHammer,
  faGear,
} from "@fortawesome/free-solid-svg-icons";

import SettingsPopup, { PreferencesContext } from "./Popups/Settings";
import ToolsPopup from "./Popups/Tools";

import lean4webConfig from "./config/config";
import "./css/Modal.css";
import "./css/Navigation.css";

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
  handleClose: () => void;
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
}> = ({ project, setProject, restart, codeMirror, setCodeMirror }) => {
  // state for handling the dropdown menus
  const [openNav, setOpenNav] = useState(false);

  // state for the popups
  const [toolsOpen, setToolsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { preferences } = useContext(PreferencesContext);

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
    </div>
  );
};
