/** Geometric botanical silhouettes — exhibition garden aesthetic. */
export function GardenBackdrop() {
  return (
    <div
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      aria-hidden
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_0%,rgba(168,181,160,0.16),transparent)]" />

      <svg
        className="absolute bottom-0 left-0 h-[50%] w-[34%] min-w-[240px] opacity-[0.42]"
        viewBox="0 0 280 320"
        fill="none"
      >
        <polygon points="60,300 60,120 100,300" fill="#6B7F6A" />
        <polygon points="45,200 75,80 105,200" fill="#8B9A7B" />
        <polygon points="35,140 70,40 105,140" fill="#A8B5A0" />
        <ellipse cx="160" cy="280" rx="48" ry="36" fill="#C9A9A6" />
        <ellipse cx="145" cy="265" rx="28" ry="22" fill="#D4B5B0" />
        <ellipse cx="178" cy="268" rx="24" ry="18" fill="#B8928E" />
        <rect x="210" y="240" width="8" height="60" fill="#B85C38" />
        <circle cx="214" cy="220" r="32" fill="#C67B5C" />
        <circle cx="198" cy="235" r="18" fill="#D4A574" />
        <rect x="0" y="298" width="280" height="4" fill="#8B9A7B" opacity="0.6" />
      </svg>

      <svg
        className="absolute bottom-0 right-0 h-[46%] w-[32%] min-w-[220px] opacity-[0.38]"
        viewBox="0 0 260 300"
        fill="none"
      >
        <path d="M200,290 Q200,180 140,100 Q200,160 260,290 Z" fill="#8B9A7B" />
        <path d="M180,290 Q190,200 120,130 Q180,190 240,290 Z" fill="#6B7F6A" />
        <rect x="40" y="180" width="24" height="110" rx="4" fill="#7A9B6E" />
        <rect x="28" y="210" width="20" height="12" rx="3" fill="#8B9A7B" />
        <rect x="56" y="230" width="18" height="10" rx="3" fill="#8B9A7B" />
        <rect x="95" y="230" width="6" height="60" fill="#6B4F2E" />
        <ellipse cx="98" cy="200" rx="42" ry="38" fill="#556652" />
        <ellipse cx="88" cy="215" rx="22" ry="18" fill="#6B7F6A" />
      </svg>

      <svg
        className="absolute right-[10%] top-[10%] h-28 w-28 opacity-[0.28]"
        viewBox="0 0 80 80"
      >
        <circle cx="40" cy="40" r="36" fill="#C9A9A6" />
        <path d="M40,8 L40,72 M8,40 L72,40" stroke="#6B7F6A" strokeWidth="3" />
        <circle cx="40" cy="40" r="12" fill="#D4B86A" />
      </svg>

      <svg
        className="absolute left-[8%] top-[22%] h-20 w-20 opacity-[0.26]"
        viewBox="0 0 64 64"
      >
        <polygon points="32,4 56,60 8,60" fill="#A8B5A0" />
        <polygon points="32,20 44,52 20,52" fill="#6B7F6A" />
      </svg>

      <svg
        className="absolute bottom-0 left-0 right-0 h-28 w-full opacity-[0.18]"
        viewBox="0 0 1200 112"
        preserveAspectRatio="none"
      >
        <path d="M0,72 L0,112 L1200,112 L1200,56 Q900,88 600,68 T0,72 Z" fill="#A8B5A0" />
        <path
          d="M0,84 L1200,68"
          stroke="#C67B5C"
          strokeWidth="2"
          strokeDasharray="10 14"
          opacity="0.7"
        />
      </svg>
    </div>
  )
}