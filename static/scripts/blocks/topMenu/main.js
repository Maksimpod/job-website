document.addEventListener('DOMContentLoaded', function(event) { 
  const activeClassName = 'active';
  const disabledClassName = 'disabled';
  const path = decodeURIComponent(window.location.pathname);
  const snapshot = document.evaluate("//nav[contains(@class, 'topMenu')]//li/a", document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
  
  for (let i = 0; i < snapshot.snapshotLength; i++) {
    const item = snapshot.snapshotItem(i);
    const itemHref = item.getAttribute('href');
    
    if (path == itemHref) {
      if (!(item.classList.contains(disabledClassName))) {
        item.classList.add(disabledClassName);
      }
    }
    
    if (path.startsWith(itemHref)) {
      if (!(item.classList.contains(activeClassName))) {
        item.classList.add(activeClassName);
        break;
      }
    }
  }
});
