document.addEventListener('DOMContentLoaded', function(event) { 
  const snapshot = document.evaluate("//a[contains(@class, 'action')]", document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
  
  for (let i = 0; i < snapshot.snapshotLength; i++) {
    const item = snapshot.snapshotItem(i);
    
    item.addEventListener('click', function() {
      if (this.classList.contains('showHidden')) {
        const hiddenItemsSnapshot = document.evaluate("(//following-sibling::*[contains(@class, 'hidden')])[1]", this, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
        if (hiddenItemsSnapshot.snapshotLength == 1) {
          const hiddenItems = hiddenItemsSnapshot.snapshotItem(0);
          
          this.remove();
          hiddenItems.classList.remove('hidden');
        }
      }
    });
  }
});
