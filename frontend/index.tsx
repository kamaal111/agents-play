import ReactDOM from 'react-dom/client';

import App from './App';
import DataProviders from './data-providers/data-providers';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error("Could not find 'root' element");

const root = ReactDOM.createRoot(rootElement);
root.render(
  <DataProviders>
    <App />
  </DataProviders>,
);
