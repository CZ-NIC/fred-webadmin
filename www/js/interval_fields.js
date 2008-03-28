function onChangeDateIntervalType(thisElem) {
	var parent_div = thisElem.parentNode;
	var interval_span = getFirstElementByTagAndClassName('span', 'date_interval', parent_div);
	var interval_offset_span = getFirstElementByTagAndClassName('span', 'date_interval_offset', parent_div);
	var day_span = getFirstElementByTagAndClassName('span', 'date_day', parent_div);
	
	switch(thisElem.value) {
		case "1":  //ccReg.DAY
			day_span.style.display = 'inline';
			interval_span.style.display = 'none';
            interval_offset_span.style.display = 'none';
			break;
		case "2": //ccReg.INTERVAL
			day_span.style.display = 'none';
			interval_span.style.display = 'inline';
			interval_offset_span.style.display = 'none';
			break;
		default:
			day_span.style.display = 'none';
			interval_span.style.display = 'none';
			interval_offset_span.style.display = 'inline';
			break;		
	}
}
