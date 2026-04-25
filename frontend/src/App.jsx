const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  return (
    <main className="container">
      <h1>ebook-manager</h1>
      <p>Interface frontend minimaliste prête pour gérer votre bibliothèque.</p>

      <section className="card">
        <h2>Backend</h2>
        <p>
          API FastAPI disponible sur: <code>{API_URL}</code>
        </p>
        <ul>
          <li>GET /health</li>
          <li>GET /ebooks</li>
          <li>POST /ebooks</li>
        </ul>
      </section>
    </main>
  )
}

export default App
