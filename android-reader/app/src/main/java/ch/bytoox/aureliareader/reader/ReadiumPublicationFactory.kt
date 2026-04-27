package ch.bytoox.aureliareader.reader

import android.content.Context
import java.io.File
import org.readium.r2.navigator.epub.EpubNavigatorFactory
import org.readium.r2.shared.ExperimentalReadiumApi
import org.readium.r2.shared.publication.Publication
import org.readium.r2.shared.publication.allAreHtml
import org.readium.r2.shared.publication.services.isRestricted
import org.readium.r2.shared.util.asset.AssetRetriever
import org.readium.r2.shared.util.getOrElse
import org.readium.r2.shared.util.http.DefaultHttpClient
import org.readium.r2.streamer.PublicationOpener
import org.readium.r2.streamer.parser.DefaultPublicationParser

data class ReadiumEpubSession(
    val publication: Publication,
    val navigatorFactory: EpubNavigatorFactory
)

@OptIn(ExperimentalReadiumApi::class)
class ReadiumPublicationFactory(context: Context) {
    private val appContext = context.applicationContext
    private val httpClient = DefaultHttpClient()
    private val assetRetriever = AssetRetriever(appContext.contentResolver, httpClient)
    private val publicationOpener = PublicationOpener(
        publicationParser = DefaultPublicationParser(
            context = appContext,
            httpClient = httpClient,
            assetRetriever = assetRetriever,
            pdfFactory = null
        )
    )

    suspend fun openEpub(file: File): ReadiumEpubSession {
        require(file.exists() && file.length() > 0L) {
            "Fichier EPUB local introuvable."
        }

        val asset = assetRetriever.retrieve(file).getOrElse { error ->
            throw IllegalStateException(error.message)
        }

        val publication = publicationOpener.open(
            asset = asset,
            allowUserInteraction = false
        ).getOrElse { error ->
            throw IllegalStateException(error.message)
        }

        if (publication.isRestricted) {
            publication.close()
            throw IllegalStateException("Ce livre est protege et ne peut pas etre ouvert pour le moment.")
        }

        if (!publication.conformsTo(Publication.Profile.EPUB) && !publication.readingOrder.allAreHtml) {
            publication.close()
            throw IllegalStateException("Format non supporte par le lecteur EPUB.")
        }

        return ReadiumEpubSession(
            publication = publication,
            navigatorFactory = EpubNavigatorFactory(publication)
        )
    }
}
