# Package media folders

Put media in the folder whose name exactly matches the package `id` in
`app/data/catalog_pdf.json`. Do not put media directly in this folder.

| Folder | Service | Package |
|---|---|---|
| `decor_hospital` | Decor | Special Hospital Decoration |
| `decor_basic` | Decor | Home Decor |
| `decor_deluxe` | Decor | Medium Home Decor |
| `decor_premium` | Decor | Premium Home Decor |
| `decor_special` | Decor | Special Home Decoration |
| `limo_grand` | Limousine | The Grand Arrival |
| `limo_special` | Limousine | Special Limousine Service |
| `limo_royal` | Limousine | Special Limousine Service Premium |
| `photo_digital` | Photography | Digital Photography |
| `photo_standard` | Photography | Standard Photography |
| `photo_premium` | Photography | Premium Photography |
| `videography` | Photography | Videography Package |

## Naming convention

Use numbered image files so the first image is the package cover:

```text
01.webp
02.webp
03.webp
```

Use a poster image and a descriptive filename for direct video files:

```text
video-poster.webp
service-video.mp4
```

Videos hosted on YouTube, Vimeo, Cloudinary, or another HTTPS provider do not
need to be copied into the project. Add their HTTPS URL to the package's
`media.videos` list in `app/data/catalog_pdf.json`. A local image is referenced
from the app as `/app/assets/media/<package-id>/<filename>`.

Example for `decor_basic`:

```json
"media": {
  "images": [
    {
      "src": "/app/assets/media/decor_basic/01.webp",
      "alt": {
        "en": "Home decoration example",
        "am": "የቤት ዲኮር ምሳሌ"
      }
    }
  ],
  "videos": [
    {
      "url": "https://www.youtube.com/watch?v=VIDEO_ID",
      "title": {
        "en": "Previous home decoration service",
        "am": "ቀደም ሲል የተሰራ የቤት ዲኮር አገልግሎት"
      }
    }
  ]
}
```
