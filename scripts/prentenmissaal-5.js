$(document).ready(function() {
    // kick off Masonry
    $('#container').masonry({
      // options
      itemSelector : '.item',
      columnWidth : 490,
      gutterWidth : 20
    }).imagesLoaded(function() {
	   $('#container').masonry('reload');
	});
});
$(window).load(function() {
    $('.thumbnailportrait').each(function(idx,img) {
      if ($(img).width() > $(img).height()) {
        $(img).removeClass('thumbnailportrait');
        $(img).addClass('thumbnaillandscape');
      }  
    });
});

/* code for google analytics */
var _gaq = _gaq || [];
_gaq.push(['_setAccount', 'UA-37368530-1']);
_gaq.push(['_trackPageview']);
(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();
