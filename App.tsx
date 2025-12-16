import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { CreateInvoice } from './pages/CreateInvoice';
import { InvoiceDetails } from './pages/InvoiceDetails';

const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreateInvoice />} />
          <Route path="/invoice/:id" element={<InvoiceDetails />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;