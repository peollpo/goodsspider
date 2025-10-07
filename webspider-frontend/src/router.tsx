import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from './components/Auth/PrivateRoute';
import MainLayout from './components/Layout/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CrawlTasks from './pages/CrawlTasks';
import Products from './pages/Products';
import Stores from './pages/Stores';
import ProductHistory from './pages/ProductHistory';
import ProductComparison from './pages/Comparison/Products';
import StoreComparison from './pages/Comparison/Stores';

const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <MainLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="crawl-tasks" element={<CrawlTasks />} />
          <Route path="products" element={<Products />} />
          <Route path="stores" element={<Stores />} />
          <Route path="product-history" element={<ProductHistory />} />
          <Route path="comparison/products" element={<ProductComparison />} />
          <Route path="comparison/stores" element={<StoreComparison />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
