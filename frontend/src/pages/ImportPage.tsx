import { ChangeEvent, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FolderUp, Loader2, RotateCcw, Upload, XCircle } from "lucide-react";
import {
  cancelImportBatch,
  listImportBatches,
  retryImportBatch,
  uploadImportBatch,
  type ImportBatch
} from "../lib/api";

function jobClass(status: string) {
  if (status === "success") {
    return "job-row success";
  }
  if (status === "warning") {
    return "job-row warning";
  }
  if (status === "failed") {
    return "job-row failed";
  }
  return "job-row";
}

function batchSummary(batch: ImportBatch) {
  return `${batch.processed_items}/${batch.total_items} - ${batch.success_count} ok, ${batch.warning_count} warning, ${batch.failed_count} echec`;
}

export function ImportPage() {
  const fileInput = useRef<HTMLInputElement | null>(null);
  const folderInput = useRef<HTMLInputElement | null>(null);
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const jobs = useQuery({
    queryKey: ["import-batches"],
    queryFn: () => listImportBatches(10),
    refetchInterval: 3000
  });

  const uploadMutation = useMutation({
    mutationFn: ({ files, paths }: { files: File[]; paths: string[] }) => uploadImportBatch(files, paths),
    onSuccess: async (result) => {
      setError(null);
      setMessage(`${result.total} EPUB ajoute(s) a la file.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["import-batches"] }),
        queryClient.invalidateQueries({ queryKey: ["books"] })
      ]);
    },
    onError: (caught) => {
      setMessage(null);
      setError(caught instanceof Error ? caught.message : "Import impossible");
    }
  });

  const cancelMutation = useMutation({
    mutationFn: cancelImportBatch,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["import-batches"] });
    }
  });

  const retryMutation = useMutation({
    mutationFn: retryImportBatch,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["import-batches"] });
    }
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []).filter((file) => file.name.toLowerCase().endsWith(".epub"));
    if (!files.length) {
      event.target.value = "";
      return;
    }
    const paths = files.map((file) => file.webkitRelativePath || file.name);
    uploadMutation.mutate({ files, paths });
    event.target.value = "";
  }

  const busy = uploadMutation.isPending;

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Gestion</p>
          <h1>Import EPUB</h1>
        </div>
      </header>
      <section className="import-panel">
        {busy ? <Loader2 className="spin" size={28} aria-hidden="true" /> : <Upload size={28} aria-hidden="true" />}
        <h2>Upload par file</h2>
        <p>Les EPUB sont ajoutes a une file persistante avec progression, logs et retry.</p>
        <input
          ref={fileInput}
          className="visually-hidden"
          type="file"
          multiple
          accept=".epub,application/epub+zip"
          onChange={handleFileChange}
        />
        <input
          ref={folderInput}
          className="visually-hidden"
          type="file"
          multiple
          accept=".epub,application/epub+zip"
          onChange={handleFileChange}
          {...({ webkitdirectory: "", directory: "" } as Record<string, string>)}
        />
        <div className="action-row">
          <button className="primary-action" disabled={busy} onClick={() => fileInput.current?.click()}>
            <Upload size={18} aria-hidden="true" />
            Fichiers EPUB
          </button>
          <button className="secondary-action" disabled={busy} onClick={() => folderInput.current?.click()}>
            <FolderUp size={18} aria-hidden="true" />
            Dossier
          </button>
        </div>
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
        <h2>File d'import</h2>
        <div className="job-list">
          {(jobs.data?.items ?? []).map((batch) => (
            <article key={batch.id} className={jobClass(batch.status)}>
              <div>
                <strong>{batch.message ?? "Import EPUB"}</strong>
                <span>{batch.status} - {Math.round(batch.progress_percent)}%</span>
              </div>
              <p>{batchSummary(batch)}</p>
              <div className="progress-track" aria-hidden="true">
                <span style={{ width: `${batch.progress_percent}%` }} />
              </div>
              <div className="row-actions">
                <button
                  className="icon-button compact-icon"
                  aria-label="Annuler"
                  disabled={cancelMutation.isPending || ["success", "warning", "failed", "canceled"].includes(batch.status)}
                  onClick={() => cancelMutation.mutate(batch.id)}
                >
                  <XCircle size={16} aria-hidden="true" />
                </button>
                <button
                  className="icon-button compact-icon"
                  aria-label="Retry"
                  disabled={retryMutation.isPending || !["failed", "canceled"].includes(batch.status)}
                  onClick={() => retryMutation.mutate(batch.id)}
                >
                  <RotateCcw size={16} aria-hidden="true" />
                </button>
              </div>
              {batch.jobs.slice(0, 5).map((job) => (
                <p key={job.id}>
                  <span>{job.filename ?? "EPUB"}</span>
                  <span>{job.status}</span>
                </p>
              ))}
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
