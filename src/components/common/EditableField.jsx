import React, { useState } from 'react';

export const EditableField = ({ id, fallback }) => {
  const [value, setValue] = useState(fallback);
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return (
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => setIsEditing(false)}
        onKeyDown={(e) => e.key === 'Enter' && setIsEditing(false)}
        autoFocus
        style={{
          fontSize: 'inherit',
          fontWeight: 'inherit',
          fontFamily: 'inherit',
          color: 'inherit',
          border: '1px solid #0a2342',
          padding: '2px 4px',
          borderRadius: '4px',
          width: '100%'
        }}
      />
    );
  }

  return (
    <span 
      onClick={() => setIsEditing(true)} 
      style={{ cursor: 'pointer', borderBottom: '1px dashed transparent' }}
      onMouseOver={(e) => e.currentTarget.style.borderBottomColor = '#ccc'}
      onMouseOut={(e) => e.currentTarget.style.borderBottomColor = 'transparent'}
    >
      {value}
    </span>
  );
};
