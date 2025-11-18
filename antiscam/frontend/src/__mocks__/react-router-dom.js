const React = require("react");

const FragmentWrapper = ({ children }) => React.createElement(React.Fragment, null, children);

const Route = ({ element = null }) => element;

const Navigate = () => null;

const useNavigate = () => () => {};

const createNoopHook = (value) => () => value;

module.exports = {
  BrowserRouter: FragmentWrapper,
  Routes: FragmentWrapper,
  Route,
  Navigate,
  Link: FragmentWrapper,
  Outlet: FragmentWrapper,
  useNavigate,
  useLocation: createNoopHook({ pathname: "/" }),
  useParams: createNoopHook({}),
};

