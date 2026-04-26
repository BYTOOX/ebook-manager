import { ChangeEvent, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FolderSearch, Loader2, Upload, XCircle } from "lucide-react";
import {
  apiFetch,
  scanIncoming,
  uploadBook,
  type ImportJobsResponse
} from "../lib/api";

export function ImportPage() {
  const fileInput = useRef<HTMLInputElement | null>(null);
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const jobs = useQuery({
    queryKey: ["import-jobs"],
    queryFn: () => apiFetch<ImportJobsResponse>("/import-jobs?limit=8")
  });

  const uploadMutation = useMutation({
    mutationFn: uploadBook,
    onSuccess: async (result) => {
      setError(null);
      setMessage(
        result.status === "warning"
          ? result.warning ?? "Doublon exact detecte."
          : "EPUB importe avec succes."
      );
      await queryClient.invalidateQueries({ queryKey: ["import-jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["books"] });
    },
    onError: (caught) => {
      setMessage(null);
      setError(caught instanceof Error ? caught.message : "Import impossible");
    }
  });

  const scanMutation = useMutation({
    mutationFn: scanIncoming,
    onSuccess: async (result) => {
      setError(null);
      setMessage(
        `${result.scanned} fichier(s) scannes, ${result.imported} importe(s), ${result.warnings} warning(s), ${result.failed} echec(s).`
      );
      await queryClient.invalidateQueries({ queryKey: ["import-jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["books"] });
    },
    onError: (caught) => {
      setMessage(null);
      setError(caught instanceof Error ? caught.message : "Scan impossible");
    }
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    void uploadMutation.mutateAsync(file);
    event.target.value = "";
  }

  const busy = uploadMutation.isPending || scanMutation.isPending;

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Gestion discrete</p>
          <h1>Import EPUB</h1>
        </div>
      </header>
      <section className="import-panel">
        {uploadMutation.isPending ? <Loader2 className="spin" size={28} aria-hidden="true" /> : <Upload size={28} aria-hidden="true" />}
        <h2>Upload EPUB</h2>
        <p>Importe un fichier EPUB, extrait les metadonnees et stocke l’original dans la bibliotheque.</p>
        <input
          ref={fileInput}
          className="visually-hidden"
          type="file"
          accept=".epub,application/epub+zip"
          onChange={handleFileChange}
        />
        <button className="primary-action" disabled={busy} onClick={() => fileInput.current?.click()}>
          <Upload size={18} aria-hidden="true" />
          Choisir un EPUB
        </button>
      </section>
      <section className="quiet-panel">
        <FolderSearch size={22} aria-hidden="true" />
        <h2>Scan incoming</h2>
        <p>Le dossier `/data/library/incoming` est scanne cote serveur.</p>
        <button className="secondary-action" disabled={busy} onClick={() => scanMutation.mutate()}>
          {scanMutation.isPending ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <FolderSearch size={18} aria-hidden="true" />}
          Scanner
        </button>
      </section>
      {message && (
        <p className="notice success">
          <CheckCircle2 size={18} aria-hidden="true" />
          {message}
        </p>
      )}
      {error && (
        <p className="notice error">
          <XCircle size={18} aria-hidden="true" />
          {error}
        </p>
      )}
      <section className="settings-section">
        <h2>Derniers imports</h2>
        <div className="job-list">
          {(jobs.data?.items ?? []).map((job) => (
            <article key={job.id} className={`job-row ${job.status}`}>
              <div>
                <strong>{job.filename ?? "Import"}</strong>
                <span>{job.source} · {job.status}</span>
              </div>
              {job.error_message && <p>{job.error_message}</p>}
            </article>
          ))}
          {!jobs.isLoading && jobs.data?.items.length === 0 && (
            <p className="muted-line">Aucun import pour le moment.</p>
          )}
        </div>
      </section>
    </main>
  );
}
