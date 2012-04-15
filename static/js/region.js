function morefeed(prop, name, isself, num) {
    var lastindex = $("#li").text();
    $("#morebtn").text("加载中...");
    $.ajax({
        type:'GET',
        url:'/more/' + prop,
        data:{lastindex:lastindex,name:name,isself:isself},
        success:function(data){
            $(".peoplelist").append(data);
            $("#li").text(parseInt(lastindex) + num);
            var hnid = "#hn"+(parseInt(lastindex) + num);
            if($(hnid).text() == "1"){
                $("#morebtn").text("更多");
            }
            else {
                $("#morebtn").hide();
            }
        }       
    });
    return false;
}
