function onChangeDateIntervalType(thisElem) {
	var parent_div = thisElem.parentNode;
	var interval_span = Ext.query('span.date_interval', parent_div)[0];
	var interval_offset_span = Ext.query('span.date_interval_offset', parent_div)[0];
	var day_span = Ext.query('span.date_day', parent_div)[0];
	
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
