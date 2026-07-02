export const colors = {
  // Backgrounds
  bg:           "#0F1117",   // near-black — primary background
  surface:      "#1A1D27",   // card / bottom sheet background
  surfaceHigh:  "#22263A",   // elevated surface (modals)

  // Brand
  primary:      "#00C896",   // teal-green — CTAs, active states
  primaryDim:   "#00C89620", // 12% alpha — tinted backgrounds

  // Accents
  warning:      "#F5A623",   // amber — reorder alerts
  danger:       "#FF4D4D",   // red — out-of-stock, errors
  info:         "#4D9EFF",   // blue — forecast, info badges

  // Text
  textPrimary:  "#FFFFFF",
  textSecondary:"#8B92A5",
  textMuted:    "#4A5065",

  // Borders
  border:       "#2A2D3E",
  borderLight:  "#363A52",
};

export const type = {
  displayLg:  { fontFamily: "Syne_700Bold",    fontSize: 28, lineHeight: 34 },
  displaySm:  { fontFamily: "Syne_700Bold",    fontSize: 22, lineHeight: 28 },
  headingMd:  { fontFamily: "Syne_600SemiBold",fontSize: 18, lineHeight: 24 },
  bodyLg:     { fontFamily: "DMSans_400Regular",fontSize: 16, lineHeight: 24 },
  bodySm:     { fontFamily: "DMSans_400Regular",fontSize: 14, lineHeight: 20 },
  label:      { fontFamily: "DMSans_500Medium", fontSize: 12, lineHeight: 16 },
  mono:       { fontFamily: "JetBrainsMono_400Regular", fontSize: 14 },
};

export const spacing = { xs:4, sm:8, md:16, lg:24, xl:32, xxl:48 };
export const radius  = { sm:8, md:12, lg:16, xl:24, full:999 };

export const shadow = {
  sm: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.18,
    shadowRadius: 1.00,
    elevation: 1,
  },
  md: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  lg: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.30,
    shadowRadius: 4.65,
    elevation: 8,
  },
};
