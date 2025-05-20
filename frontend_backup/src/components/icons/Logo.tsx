import type React from 'react';

const Logo: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 200 50"
    width="120"
    height="30"
    {...props}
    aria-label="Web Agent Weaver Logo"
  >
    <defs>
      <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style={{ stopColor: 'hsl(var(--primary))', stopOpacity: 1 }} />
        <stop offset="100%" style={{ stopColor: 'hsl(var(--accent))', stopOpacity: 1 }} />
      </linearGradient>
    </defs>
    <rect width="200" height="50" rx="5" fill="transparent" />
    <text
      x="10"
      y="35"
      fontFamily="Inter, Arial, sans-serif"
      fontSize="28"
      fontWeight="bold"
      fill="url(#logoGradient)"
    >
      Web Agent Weaver
    </text>
  </svg>
);

export default Logo;
