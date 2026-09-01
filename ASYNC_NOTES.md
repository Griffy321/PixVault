# Where to bring in async / more advanced Python

Notes on the saving, images, and videos work — where the current code blocks
sequentially and where `asyncio`, threads, or generators would actually pay off.
Written against the code as it stands (stubs included), not a rewrite plan.

## Why this app is a good fit

Everything slow in PixVault is I/O, not CPU:
- `adb` calls are subprocesses (`device/adb.py`) — listing a folder, sizing files,
  pulling a file. Each one blocks on the device/USB connection.
- Local folder scanning (`local/folder.py`) walks the filesystem and stats every entry.
- Image/video preview decoding (`visualisation/images.py`, `visualisation/videos.py`)
  will block on file reads + `cv2` decode once implemented.

None of this benefits from true parallelism (no GIL-bound crunching), so
`asyncio` — or a thread pool if you want to keep using the blocking `adb`/`cv2`
calls as-is — is the right tool, not multiprocessing.

One Qt-specific catch: PySide6 has its own event loop. Plain `asyncio.run()`
inside a Qt app will fight the Qt loop. You'll want **`qasync`** (bridges
asyncio into Qt's event loop) or keep async work in a background thread and
signal results back to the UI thread with Qt signals. Worth deciding that
early since it shapes every item below.

---

## 2. `device/saving.py` — `FileSaving.saveAll()` and `saveFile()`

This is the biggest win in the app.

- `saveAll()` (lines 108-117) is a plain generator that calls `saveFile()` once
  per item in `self.toBackup`, strictly sequentially — one `adb pull` finishes
  entirely before the next starts.
- Turn this into an **async generator** (`async def saveAll(self)` with `yield`
  inside) driven by `asyncio.gather()` or a bounded `asyncio.Semaphore` (e.g.
  3-4 concurrent pulls) over `saveFile()`. adb can genuinely serve overlapping
  pulls, so this should meaningfully cut backup time on larger batches.
- `transferredBytes` (line 116) is mutated per-completed-file today, which is
  safe sequentially but becomes a shared-state concern once pulls run
  concurrently — either guard it or have each task report its own delta back
  through an `asyncio.Queue` that a single coroutine tallies.
- `verifySaved()` and `saveFile()` (lines 83-105) are natural `async def`s once
  `adb.pullFiles` has an async counterpart from item 1.

## 3. `local/folder.py` — `LocalFolder.loadPCFolderContent()` / `walkFiles()`

- `walkFiles()` (lines 78-98) is a synchronous generator over `os.scandir`, and
  `loadPCFolderContent()` (lines 111-124) calls `entry.stat()` on every media
  file it finds. On a large backup destination this is a lot of blocking
  syscalls in a row.
- This one's less about `asyncio` (filesystem I/O doesn't get much from an
  event loop) and more about a **thread pool** — `concurrent.futures.ThreadPoolExecutor`
  or `asyncio.to_thread()` to stat files in parallel, since `stat()` calls are
  independent of each other.
- Practical middle ground: keep `walkFiles` as is (directory traversal is
  already cheap), but batch the `entry.stat()` calls in `loadPCFolderContent`
  through a thread pool so they overlap instead of running one at a time.

## 4. `app/saving_view.py` — `SavingScreen`, especially `cachePreview()`

This is the screen you're about to build out, and it's the one place where
async directly improves *felt* responsiveness, not just total runtime.

- `cachePreview()` (line 119): "Pulls fileName to a local temp copy so it can
  be previewed" — this is an `adb pull` done just to show a card. Today the
  natural implementation blocks the UI while the pull happens.
- The fix is **prefetching**: while the user is looking at card N, kick off
  `cachePreview()` for card N+1 (and maybe N+2) in the background, so by the
  time they swipe, the file's already local. This is the textbook case for
  `asyncio.create_task()` — fire off the next pull, don't await it immediately,
  await it only when `advance()` actually needs the file.
- `showCard()` (line 114) and `advance()` (line 109) would then need to check
  "is the prefetch for this card done yet" rather than assuming the file is
  already there — worth designing the queue/cache as `{fileName: asyncio.Task}`
  so `showCard` can `await` a task that may already be finished.
- `showToast()` (line 124) — "drops the banner down... then hides it again" —
  is a timed UI animation, not I/O, so `QTimer` is the right tool there, not
  asyncio. Worth not reaching for async just because it's on this screen.

## 5. `visualisation/images.py` / `visualisation/videos.py` — still stubs

Both `OpenImage.showLoadedImage()` and `OpenVideo.showLoadedImage()` are
unimplemented `pass` bodies right now, so this is the cheapest place to start
async-native rather than retrofit later:

- Decoding an image with `cv2.imread` and grabbing a frame from a video with
  `cv2.VideoCapture` are both blocking calls. Wrap them as `async def` methods
  that run the actual `cv2` call via `asyncio.to_thread()` (cv2 releases the
  GIL during its C calls, so a thread pool genuinely parallelizes this too).
- Video frame extraction in particular is the more expensive of the two —
  worth caching the extracted frame per file (keyed on path) so flipping back
  to a previously-seen card in `SavingScreen` doesn't redecode.
- If prefetching (item 4) hands `cachePreview()` a local temp file before the
  card is shown, these two classes can also start decoding during that same
  prefetch window instead of only starting once the file lands.

## 6. Shape of it end to end

If you want the concurrency to compose cleanly rather than being four
unrelated patches, the natural pipeline for the saving screen is:

```
dedupe (buildBackupList, sync, fast)
   -> prefetch queue: cachePreview() tasks, N ahead of the current card
        -> decode queue: OpenImage/OpenVideo tasks, feeding off prefetched files
             -> SavingScreen shows whichever card's decode has completed
```

Each arrow is a producer/consumer relationship, which is where an
`asyncio.Queue` per stage (or a single `asyncio.Semaphore`-bounded task pool)
fits better than manually tracking task objects per file. `saveAll()` (item 2)
is a separate, simpler pipeline — just a bounded-concurrency pull, no decode
step — so it doesn't need to share the same queue machinery.

## Suggested order

1. `device/adb.py` async subprocess wrapper (item 1) — everything else needs it.
2. `FileSaving.saveAll()` concurrent pulls (item 2) — immediate, measurable win,
   and exercises the new adb layer.
3. `SavingScreen.cachePreview()` prefetching (item 4) — the one that makes the
   screen you're building actually feel fast.
4. `OpenImage` / `OpenVideo` async decode (item 5) — do this while you're
   implementing them anyway, rather than writing them sync and circling back.
5. `LocalFolder` stat batching (item 3) — lowest urgency, only matters once
   destination folders get large.
