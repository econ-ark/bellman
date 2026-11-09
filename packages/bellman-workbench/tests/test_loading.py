"""The Workbench startup mark before and after the kernel answers."""

import base64

import pytest


LOADER = "#loader-container"
MARK = f"{LOADER} #sun-spinner-container"
ART = "/static/assets/brand/loading.svg"

PAINTED_HALVES = """
async (png) => {
  const image = new Image();
  image.src = 'data:image/png;base64,' + png;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.width;
  canvas.height = image.height;
  const context = canvas.getContext('2d');
  context.drawImage(image, 0, 0);
  const counts = [0, 0];
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
  for (let i = 0; i < pixels.length; i += 4) {
    if (pixels[i + 1] > 100 && pixels[i + 2] > 100) {
      counts[Number((i / 4) % canvas.width >= canvas.width / 2)]++;
    }
  }
  return counts;
}
"""


@pytest.mark.parametrize("width,height,motion", [(960, 640, "no-preference"), (320, 480, "reduce")])
def test_startup_mark_and_kernel_handoff(browser, server_on, durables_folder, tmp_path, width, height, motion):
    context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion=motion)
    page = context.new_page()
    queued = []
    holding = True
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def hold_kernel(route):
        server = route.connect_to_server()

        def receive(message):
            if holding:
                queued.append((route, message))
            else:
                route.send(message)

        server.on_message(receive)

    def release_kernel():
        nonlocal holding
        holding = False
        for route, message in queued:
            route.send(message)
        queued.clear()
        page.locator(".bl-root").wait_for(timeout=20_000)
        page.locator(LOADER).wait_for(state="detached", timeout=8_000)

    page.route_web_socket("**/jupyter/api/kernels/*/channels**", hold_kernel)
    try:
        page.goto(server_on(durables_folder), wait_until="domcontentloaded")
        loader = page.locator(LOADER)
        mark = page.locator(MARK)
        loader.wait_for(timeout=12_000)
        assert "Loading" in loader.locator("h1").inner_text()
        assert page.locator(".bl-root").count() == 0
        assert ART in mark.evaluate("element => getComputedStyle(element).backgroundImage")
        assert page.title() == "Bellman Workbench"
        style = loader.evaluate("""element => {
          const {position, backgroundColor, zIndex} = getComputedStyle(element);
          return [position, backgroundColor, zIndex];
        }""")
        assert style == ["fixed", "rgb(15, 27, 54)", "1"]
        assert "Archivo" in loader.locator("h1").evaluate("element => getComputedStyle(element).fontFamily")
        assert not loader.locator("#sun-spinner1").is_visible()
        assert not loader.locator("#sun-spinner2").is_visible()
        page.wait_for_function(
            "path => performance.getEntriesByType('resource').some(entry => new URL(entry.name).pathname === path)",
            arg=ART,
        )
        early = mark.screenshot(animations="allow")
        page.screenshot(path=tmp_path / "startup-early.png", animations="allow")
        page.wait_for_timeout(2_900 if motion == "no-preference" else 700)
        finished = mark.screenshot(animations="allow")
        page.screenshot(path=tmp_path / "startup-finished.png", animations="allow")
        halves = page.evaluate(PAINTED_HALVES, base64.b64encode(finished).decode("ascii"))
        assert min(halves) > 30, halves
        bounds = mark.bounding_box()
        assert bounds is not None
        assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width
        assert bounds["y"] >= 0 and bounds["y"] + bounds["height"] <= height
        assert (early == finished) == (motion == "reduce")
        assert finished == mark.screenshot(animations="allow")
        if motion == "reduce":
            assert loader.evaluate("""element => {
              const leave = 'solara-transition-leave-active';
              element.classList.add(leave);
              const duration = getComputedStyle(element).transitionDuration;
              element.classList.remove(leave);
              return duration;
            }""") == "0s"
        assert queued and loader.is_visible()
        release_kernel()

        if motion == "no-preference":
            assert page.evaluate("() => solara.debug.dropConnection()")
            page.wait_for_function(
                "() => solara.debug.reconnectCount >= 1 && solara.debug.viewMounted()", timeout=15_000
            )
            assert loader.count() == 0
            holding = True
            page.reload(wait_until="domcontentloaded")
            loader.wait_for(timeout=12_000)
            assert loader.count() == 1 and page.locator(".bl-root").count() == 0
            release_kernel()

        assert errors == []
    finally:
        context.close()
