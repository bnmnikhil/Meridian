const form = document.querySelector("#review-form");
const loadingPanel = document.querySelector("#loading-panel");
const runButton = document.querySelector("#run-button");
const sourcePreview = document.querySelector("#source-preview");
const previewFileName = document.querySelector("#preview-file-name");
const sourceContentElement = document.querySelector("#context-source-content");

if (sourcePreview && previewFileName && sourceContentElement) {
  const sourceContents = JSON.parse(sourceContentElement.textContent);
  const sourceButtons = document.querySelectorAll(".source-button");

  sourceButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const sourceName = button.dataset.sourceName;
      if (!Object.prototype.hasOwnProperty.call(sourceContents, sourceName)) return;

      sourcePreview.textContent = sourceContents[sourceName];
      previewFileName.textContent = sourceName;
      sourceButtons.forEach((item) => {
        item.setAttribute("aria-pressed", String(item === button));
      });
    });
  });
}

if (form && loadingPanel && runButton) {
  form.addEventListener("submit", () => {
    loadingPanel.hidden = false;
    document.body.classList.add("is-loading");
    runButton.disabled = true;
    runButton.innerHTML = "Reviewing evidence…";
    loadingPanel.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}
