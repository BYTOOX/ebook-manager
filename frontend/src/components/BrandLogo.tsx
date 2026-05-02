type BrandLogoVariant = "full" | "small" | "icon";

const logoSources: Record<BrandLogoVariant, string> = {
  full: "/brand/aurelia-logo-full.png",
  small: "/brand/aurelia-logo-small.png",
  icon: "/brand/aurelia-icon.png"
};

type BrandLogoProps = {
  variant?: BrandLogoVariant;
  className?: string;
  label?: string;
  decorative?: boolean;
};

export function BrandLogo({ variant = "icon", className, label = "Aurelia", decorative = false }: BrandLogoProps) {
  const classes = ["brand-logo", `brand-logo-${variant}`, className].filter(Boolean).join(" ");

  return (
    <img
      className={classes}
      src={logoSources[variant]}
      alt={decorative ? "" : label}
      aria-hidden={decorative ? "true" : undefined}
      decoding="async"
    />
  );
}
