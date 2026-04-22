export const NAVY = '#0a2342';
export const NAVY_DARK = '#051222';
export const NAVY_LIGHT = '#154175';
export const BLUE = '#3498db';
export const GREEN = '#00a896';
export const BG_LIGHT = '#f8f9fa';
export const TEXT_MAIN = '#212529';
export const TEXT_SUB = '#6c757d';
export const ACCENT = '#e63946';
export const BORDER = '#dee2e6';

export const section = {
    marginBottom: '2.5rem',
    background: '#fff',
    padding: '2rem',
    borderRadius: '1rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
};

export const sTitle = {
    fontSize: '1.5rem',
    fontWeight: '800',
    color: NAVY,
    marginBottom: '1.5rem',
    paddingBottom: '0.75rem',
    borderBottom: `3px solid ${NAVY_LIGHT}`
};

export const tbl = {
    width: '100%',
    borderCollapse: 'collapse',
    marginBottom: '1rem'
};

export const thStyle = {
    background: NAVY,
    color: '#fff',
    padding: '0.75rem 1rem',
    textAlign: 'left',
    fontSize: '0.875rem'
};

export const thC = {
    ...thStyle,
    textAlign: 'center'
};

export const thR = {
    ...thStyle,
    textAlign: 'right'
};

export const tdStyle = {
    padding: '0.75rem 1rem',
    borderBottom: `1px solid ${BORDER}`,
    fontSize: '0.875rem',
    color: TEXT_MAIN
};

export const tdR = {
    ...tdStyle,
    textAlign: 'right'
};

export const tdC = {
    ...tdStyle,
    textAlign: 'center'
};

export const tdBold = {
    ...tdStyle,
    fontWeight: '700'
};

export const zebraRow = (i) => ({
    background: i % 2 === 0 ? '#fff' : BG_LIGHT
});

export const execSummaryGrad = {
    background: `linear-gradient(135deg, ${NAVY_DARK} 0%, ${NAVY} 100%)`,
    color: '#fff',
    padding: '2rem',
    borderRadius: '1rem',
    position: 'relative',
    overflow: 'hidden'
};

export const execLabel = {
    display: 'inline-block',
    background: ACCENT,
    color: '#fff',
    padding: '0.25rem 0.75rem',
    borderRadius: '0.25rem',
    fontSize: '0.75rem',
    fontWeight: '700',
    marginBottom: '1rem'
};

export const kpiGrid = {
    display: 'grid',
    gap: '1rem'
};

export const kpiCard = {
    background: BG_LIGHT,
    padding: '1.25rem',
    borderRadius: '0.75rem',
    border: `1px solid ${BORDER}`
};

export const kpiLabel = {
    fontSize: '0.75rem',
    color: TEXT_SUB,
    marginBottom: '0.25rem',
    fontWeight: '600'
};

export const kpiValue = {
    fontSize: '1.5rem',
    fontWeight: '800'
};

export const kpiSub = {
    fontSize: '0.75rem',
    color: TEXT_SUB,
    marginTop: '0.25rem'
};

export const callout = {
    background: '#fff3cd',
    borderLeft: '4px solid #ffc107',
    padding: '1rem',
    borderRadius: '0.25rem',
    fontSize: '0.875rem',
    color: '#856404'
};

export const subHeading = {
    fontSize: '1.125rem',
    fontWeight: '700',
    color: NAVY,
    marginBottom: '1rem',
    marginTop: '1.5rem'
};

export const sourceSection = {
    marginTop: '3rem',
    paddingTop: '1.5rem',
    borderTop: `1px solid ${BORDER}`
};

export const sourceLabel = {
    fontSize: '0.75rem',
    fontWeight: '800',
    color: TEXT_SUB,
    marginBottom: '0.5rem'
};

export const sourceList = {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    fontSize: '0.75rem',
    color: TEXT_SUB,
    lineHeight: 1.6
};
