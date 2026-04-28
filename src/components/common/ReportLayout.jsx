import React from 'react';

const ReportLayout = ({ children, type, title, subtitle, date, version, audience }) => {
  return (
    <div style={{
      fontFamily: '"Pretendard", "Inter", sans-serif',
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '2rem',
      backgroundColor: '#f0f2f5',
      minHeight: '100vh'
    }}>
      <header style={{ marginBottom: '3rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <span style={{
            backgroundColor: '#0a2342',
            color: '#fff',
            padding: '0.25rem 0.75rem',
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: 'bold'
          }}>{type}</span>
          <div style={{ fontSize: '0.75rem', color: '#6c757d' }}>
            {date} | {version} | {audience}
          </div>
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '900', color: '#0a2342', marginBottom: '0.5rem' }}>{title}</h1>
        <p style={{ fontSize: '1.125rem', color: '#6c757d' }}>{subtitle}</p>
      </header>
      <main>
        {children}
      </main>
      <footer style={{ marginTop: '4rem', textAlign: 'center', color: '#adb5bd', fontSize: '0.875rem' }}>
        © 2026 Picoinnovation. All rights reserved.
      </footer>
    </div>
  );
};

export default ReportLayout;
