import { useEffect, useState, type ImgHTMLAttributes, type ReactNode } from "react";
import { authHeadersForUrl } from "../lib/api";

type AuthenticatedImageProps = Omit<ImgHTMLAttributes<HTMLImageElement>, "src"> & {
  src: string | null;
  fallback?: ReactNode;
};

export function AuthenticatedImage({ src, fallback = null, ...props }: AuthenticatedImageProps) {
  const [resolvedSrc, setResolvedSrc] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    let objectUrl: string | null = null;

    setResolvedSrc(null);
    if (!src) {
      return;
    }

    const headers = authHeadersForUrl(src);
    if (!headers.has("Authorization")) {
      setResolvedSrc(src);
      return;
    }

    fetch(src, { headers })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Image unavailable");
        }
        return response.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (alive) {
          setResolvedSrc(objectUrl);
        } else {
          URL.revokeObjectURL(objectUrl);
        }
      })
      .catch(() => {
        if (alive) {
          setResolvedSrc(null);
        }
      });

    return () => {
      alive = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [src]);

  if (!resolvedSrc) {
    return <>{fallback}</>;
  }

  return <img {...props} src={resolvedSrc} />;
}
