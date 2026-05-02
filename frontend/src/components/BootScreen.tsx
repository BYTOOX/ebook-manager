import { BrandLogo } from "./BrandLogo";

export function BootScreen() {
  return (
    <main className="boot-screen" aria-label="Chargement Aurelia">
      <BrandLogo variant="small" className="boot-logo" label="Aurelia EPUB Reader" />
      <p>Chargement</p>
    </main>
  );
}
