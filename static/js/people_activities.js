$(document).ready(function() {
    $backToTopFun = function() {
        var st = $(document).scrollTop(), winh = $(window).height();
        (st > 0)?$('#totop').show():$('#totop').hide();
    };
    $(window).bind("scroll", $backToTopFun);
    $(function() { $backToTopFun(); });
});
function backtotop() {
    $('html, body').animate({scrollTop:0}, 'fast');
    return false;
}

