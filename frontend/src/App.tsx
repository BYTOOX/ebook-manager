import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { BootScreen } from "./components/BootScreen";
import { useAuth } from "./providers/AuthProvider";
import { BookDetailPage } from "./pages/BookDetailPage";
import { CollectionsPage } from "./pages/CollectionsPage";
import { HomePage } from "./pages/HomePage";
import { ImportPage } from "./pages/ImportPage";
import { LibraryPage } from "./pages/LibraryPage";
import { LoginPage } from "./pages/LoginPage";
import { ReaderPage } from "./pages/ReaderPage";
import { SearchPage } from "./pages/SearchPage";
import { AdvancedSettingsPage, SettingsPage } from "./pages/SettingsPage";

export default function App() {
  const { status } = useAuth();

  if (status === "loading") {
    return <BootScreen />;
  }

  if (status === "anonymous") {
    return <LoginPage />;
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/collections" element={<CollectionsPage />} />
        <Route path="/books/:bookId" element={<BookDetailPage />} />
        <Route path="/reader/:bookId" element={<ReaderPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/settings/advanced" element={<AdvancedSettingsPage />} />
        <Route path="/import" element={<ImportPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
