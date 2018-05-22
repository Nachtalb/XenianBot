%for category in categories.values():
    <b>${category['title']}</b><br>
    <i>Tag: </i><code>${category['tag']}</code><br>
    <pre>Documents: ${category['document']}
        Videos: ${category['video']}
        Photos: ${category['photo']}
        Stickers: ${category['sticker']}
        Audios: ${category['audio']}
        Voices: ${category['voice']}
        Texts: ${category['text']}</pre>
    <br>
%endfor
<br>
Keep in mind that in Telegram some videos are saved as documents too, so are voices as audios and vis versa.
