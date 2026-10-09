document.querySelectorAll('[data-scanner-filters]').forEach((form) => {
  const institution = form.querySelector('[name="institution_id"]');
  const series = form.querySelector('[name="series_name"]');
  const year = form.querySelector('[name="school_year"]');
  const schoolClass = form.querySelector('[name="class_id"]');
  const filterClasses = () => {
    for (const option of schoolClass.options) {
      if (!option.value) continue;
      option.hidden = Boolean(
        (institution?.value && option.dataset.institution !== institution.value) ||
        (series.value && option.dataset.series !== series.value) ||
        (year.value && option.dataset.year !== year.value)
      );
      option.disabled = option.hidden;
    }
    if (schoolClass.selectedOptions[0]?.disabled) schoolClass.value = '';
  };
  institution?.addEventListener('change', () => {
    series.value = '';
    year.value = '';
    schoolClass.value = '';
    form.requestSubmit();
  });
  series.addEventListener('change', filterClasses);
  year.addEventListener('change', filterClasses);
  filterClasses();
});

document.querySelectorAll('[data-scan-upload]').forEach((form) => {
  form.addEventListener('submit', () => {
    form.querySelector('button[type="submit"]').disabled = true;
    form.querySelector('.scan-upload-progress').hidden = false;
  });
});
