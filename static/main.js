function showLoadingSpinner() {
    document.getElementById('spinner').style.display = 'block';
  }
function guardAnalyze(e) {
    showLoadingSpinner();
    return true;
  }