function toggle_interva_day(thisElem) {
	var parent_div = thisElem.parentNode;
	var interval_span = getFirstElementByTagAndClassName('span', 'date_interval', parent_div);
	var day_span = getFirstElementByTagAndClassName('span', 'date_day', parent_div);
	if (interval_span.style.display == 'none') {
		interval_span.style.display = 'inline';
		day_span.style.display = 'none';
	} else {
		interval_span.style.display = 'none';
		day_span.style.display = 'inline';
	}
}