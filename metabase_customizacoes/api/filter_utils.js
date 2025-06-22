(function(){
  const listeners = [];
  let currentFilters = {};

  function readDomFilters() {
    const result = {};
    try {
      const doc = window.parent.document;
      const widgets = doc.querySelectorAll('[data-dashboard-filter], .dashboard-filter, [data-testid="dashboard-filter"]');
      widgets.forEach(w => {
        let name = w.getAttribute('data-dashboard-filter') || w.getAttribute('data-filter') || w.getAttribute('data-column');
        if (!name) {
          const label = w.querySelector('label');
          if (label) name = label.getAttribute('for');
        }
        const input = w.querySelector('input, select');
        if (name && input && input.value) {
          result[name] = input.value;
        }
      });
    } catch (e) {
      console.error('Unable to read filters', e);
    }
    return result;
  }

  function checkFilters() {
    const newFilters = readDomFilters();
    if (JSON.stringify(newFilters) !== JSON.stringify(currentFilters)) {
      currentFilters = newFilters;
      listeners.forEach(fn => fn({ ...currentFilters }));
    }
  }

  window.getDashboardFilters = function() {
    return { ...currentFilters };
  };

  window.onDashboardFiltersChange = function(cb) {
    if (typeof cb === 'function') listeners.push(cb);
  };

  document.addEventListener('DOMContentLoaded', checkFilters);
  setInterval(checkFilters, 500);
})();
