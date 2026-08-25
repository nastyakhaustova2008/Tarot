/* Taro — sharing predictions as screenshots or text.
   Requires html2canvas (loaded in base.html before this file).

   Buttons don't use inline onclick with embedded text anymore — AI-generated
   text can contain quotes/newlines that break out of an HTML attribute.
   Instead each share button carries data-* attributes, and any text it needs
   lives in a sibling <script type="application/json"> tag (the safe place
   for Flask's |tojson filter). We read it here and dispatch accordingly.

   Two hard-won lessons baked into this file:

   1. Pre-capture screenshots on page load, not on click. navigator.share()
      must run as part of an active user gesture, and html2canvas is genuinely
      async — waiting until the click to start it burns through the gesture
      before share() ever gets called. So every [data-share-image] button's
      screenshot is captured ahead of time (see prepareAllShareBlobs at the
      bottom), and the click handler shares an already-resolved blob.

   2. NEVER call navigator.share() twice for the same click. Chrome consumes
      the user gesture on the FIRST share() call, whether it succeeds or
      fails — so a "fallback" call to navigator.share() after a failed file
      share always dies with "Must be handling a user gesture to perform a
      share request," no matter how quickly it's attempted. If file-sharing
      fails, the only safe fallback is a plain download + clipboard copy,
      not a second share() call. A text-only share() is only ever the FIRST
      and ONLY share() attempt for its click (that's why Yes/No and
      Questions, which never touch files, have always worked). */

// Guards against overlapping share attempts.
var shareInProgress = false;

// elementId -> Promise<Blob>, populated eagerly for every share-image
// button found on the page (see the bottom of this file).
var preparedShareBlobs = {};

function captureElementAsBlob(el) {
    return html2canvas(el, {
        backgroundColor: "#05080a",   // matches site background, no transparent holes
        scale: 2,                     // sharper screenshot
        useCORS: true
    }).then(function (canvas) {
        return new Promise(function (resolve) {
            canvas.toBlob(resolve, "image/png");
        });
    });
}

function downloadBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
}

/**
 * Downloads the image and, if there's caption text, copies it to the
 * clipboard too. This is the ONLY fallback used after a file-share
 * attempt fails — it must never call navigator.share() again (see note
 * #2 at the top of this file).
 */
function downloadWithClipboardCaption(blob, filename, text) {
    downloadBlob(blob, filename);
    if (text && navigator.clipboard) {
        navigator.clipboard.writeText(text).catch(function () {});
    }
}

/**
 * Shares a PNG file (+ optional caption text, e.g. the AI response) via
 * Web Share API, or falls back to downloading the image if file-sharing
 * isn't supported or fails. The caption is sent as the share message,
 * never drawn onto the image itself.
 */
function shareImageBlob(blob, filename, text) {
    var file = new File([blob], filename, { type: "image/png" });
    var canShareFiles = !!(navigator.canShare && navigator.canShare({ files: [file] }));
    console.log("[share debug] canShare files:", canShareFiles, "| has navigator.share:", !!navigator.share);

    if (canShareFiles) {
        return navigator.share({
            files: [file],
            text: text || undefined,
            title: "Taro"
        }).catch(function (err) {
            console.error("[share debug] navigator.share (files) failed:", err.name, err.message);
            // Do NOT call navigator.share() again here — the gesture is gone.
            downloadWithClipboardCaption(blob, filename, text);
        });
    } else {
        // No file-share attempt was made yet, so a text-only share() here
        // is still the FIRST call for this click — safe to try.
        if (navigator.share) {
            return navigator.share({ text: text || undefined, title: "Taro" }).catch(function (err) {
                console.error("[share debug] navigator.share (text, no file support) failed:", err.name, err.message);
                downloadWithClipboardCaption(blob, filename, text);
            });
        }
        downloadWithClipboardCaption(blob, filename, text);
        return Promise.resolve();
    }
}

/**
 * Puts a button into a disabled "..." state and returns a restore function.
 */
function setButtonBusy(btn) {
    if (!btn) return function () {};
    var originalText = btn.textContent;
    var originalDisabled = btn.disabled;
    btn.disabled = true;
    btn.textContent = "...";
    return function restore() {
        btn.disabled = originalDisabled;
        btn.textContent = originalText;
    };
}

/**
 * Kicks off (or returns the already-running) screenshot capture for a
 * given element, cached by elementId so it's ready well before the user
 * clicks Share.
 */
function prepareShareBlob(elementId) {
    if (preparedShareBlobs[elementId]) return preparedShareBlobs[elementId];
    var el = document.getElementById(elementId);
    if (!el) return null;
    var promise = Promise.resolve().then(function () {
        return captureElementAsBlob(el);
    }).catch(function (err) {
        console.error("[share debug] pre-capture failed for #" + elementId + ":", err);
        return null; // let the click handler notice the null and retry
    });
    preparedShareBlobs[elementId] = promise;
    return promise;
}

/**
 * Shares the pre-captured (or freshly captured) screenshot of elementId,
 * attaching extraText as the share message (e.g. the AI oracle response).
 */
function shareElement(elementId, extraText, filename, btn) {
    if (shareInProgress) {
        console.warn("[share debug] shareElement ignored — a share is already in progress");
        return;
    }
    var blobPromise = preparedShareBlobs[elementId] || prepareShareBlob(elementId);
    if (!blobPromise) return;

    shareInProgress = true;
    var restoreButton = setButtonBusy(btn);
    blobPromise.then(function (blob) {
        if (!blob) {
            var el = document.getElementById(elementId);
            if (!el) return;
            return captureElementAsBlob(el).then(function (freshBlob) {
                return shareImageBlob(freshBlob, filename, extraText || null);
            });
        }
        return shareImageBlob(blob, filename, extraText || null);
    }).catch(function (err) {
        console.error("[share debug] share failed:", err);
    }).finally(function () {
        shareInProgress = false;
        restoreButton();
        // Refresh the cached capture in the background in case the user
        // shares the same element again later.
        delete preparedShareBlobs[elementId];
        prepareShareBlob(elementId);
    });
}

/** Shares plain text only (no screenshot) — always the first and only
 *  share() call for its click, so this one is safe as-is. */
function shareText(text, btn) {
    if (shareInProgress) {
        console.warn("[share debug] shareText ignored — a share is already in progress");
        return;
    }
    shareInProgress = true;
    var restoreButton = setButtonBusy(btn);

    Promise.resolve().then(function () {
        if (navigator.share) {
            return navigator.share({ text: text, title: "Taro" }).catch(function (err) {
                console.error("[share debug] navigator.share (text only) failed:", err.name, err.message);
            });
        } else if (navigator.clipboard) {
            return navigator.clipboard.writeText(text).then(function () {
                alert("Copied to clipboard");
            }).catch(function () {});
        } else {
            alert(text);
        }
    }).catch(function (err) {
        console.error("[share debug] shareText failed:", err);
    }).finally(function () {
        shareInProgress = false;
        restoreButton();
    });
}

function readJsonScript(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
        return JSON.parse(el.textContent);
    } catch (e) {
        return null;
    }
}

/* Event delegation: works for buttons present on page load AND any
   added later, no need to wire up each button individually. */
if (!window.__taroShareListenerBound) {
    window.__taroShareListenerBound = true;

    document.addEventListener("click", function (event) {
        var btn = event.target.closest("[data-share-image], [data-share-text-src]");
        if (!btn) return;

        if (btn.dataset.shareImage) {
            var caption = btn.dataset.shareCaptionSrc ? readJsonScript(btn.dataset.shareCaptionSrc) : null;
            shareElement(btn.dataset.shareImage, caption, btn.dataset.shareFilename || "taro.png", btn);
        } else if (btn.dataset.shareTextSrc) {
            var text = readJsonScript(btn.dataset.shareTextSrc) || "";
            shareText(text, btn);
        }
    });
}

/* Eagerly warm up every image-share button's screenshot as soon as the
   page is ready, so it's already resolved by the time anyone clicks. */
function prepareAllShareBlobs() {
    document.querySelectorAll("[data-share-image]").forEach(function (btn) {
        prepareShareBlob(btn.dataset.shareImage);
    });
}
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", prepareAllShareBlobs);
} else {
    prepareAllShareBlobs();
}