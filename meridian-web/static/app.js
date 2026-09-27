const form = document.querySelector("#review-form");
const loadingPanel = document.querySelector("#loading-panel");
const runButton = document.querySelector("#run-button");

if (form && loadingPanel && runButton) {
  form.addEventListener("submit", () => {
    loadingPanel.hidden = false;
    document.body.classList.add("is-loading");
    runButton.disabled = true;
    runButton.innerHTML = "Reviewing evidence…";
    loadingPanel.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}
