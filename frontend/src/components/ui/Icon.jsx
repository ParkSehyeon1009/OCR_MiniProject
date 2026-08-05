const PATHS = {
  home: <><path d="M3 10.5 12 3l9 7.5" /><path d="M5.5 9.5V21h13V9.5" /><path d="M9 21v-7h6v7" /></>,
  documents: <><path d="M7 3h8l4 4v14H7z" /><path d="M15 3v5h5" /><path d="M10 13h6M10 17h6" /></>,
  upload: <><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M4 15v5h16v-5" /></>,
  compare: <><path d="M8 4H4v16h4" /><path d="M16 4h4v16h-4" /><path d="M9 8h6M9 12h6M9 16h6" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m16 16 5 5" /></>,
  arrowRight: <><path d="M5 12h14" /><path d="m14 7 5 5-5 5" /></>,
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 21c.8-4.2 3.5-6 8-6s7.2 1.8 8 6" /></>,
  sparkles: <><path d="m12 3 1.3 3.7L17 8l-3.7 1.3L12 13l-1.3-3.7L7 8l3.7-1.3z" /><path d="m5 14 .8 2.2L8 17l-2.2.8L5 20l-.8-2.2L2 17l2.2-.8z" /><path d="m19 13 .6 1.4L21 15l-1.4.6L19 17l-.6-1.4L17 15l1.4-.6z" /></>,
  shield: <><path d="M12 3 5 6v5c0 4.6 2.8 8.2 7 10 4.2-1.8 7-5.4 7-10V6z" /><path d="m9 12 2 2 4-4" /></>,
  check: <path d="m5 12 4 4L19 6" />,
}

export default function Icon({ name, size = 20, className = '' }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name] || PATHS.documents}
    </svg>
  )
}
