document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("auto-save-sred");
  if (!button) {
    console.warn("Button #auto-save-sred not found in DOM");
    return;
  }

  button.addEventListener("click", async () => {
    console.log("Auto save to SRED clicked");
    const response = await fetch("/auto_save_sred", { method: "POST" });
    const data = await response.json();
    console.log(data);
  });
});
