// 
$(document).ready(function() {
  $(".set > a").on("click", function() {
    $(".set > a button").on("click", function(e) {
      e.stopPropagation();
    });
    if ($(this).hasClass("active")) {
      $(this).removeClass("active");
      $(this).siblings(".content").slideUp(200);
      $(".set > a i#plus").removeClass("fa-minus").addClass("fa-plus");
      $(".set > a button").removeClass("active");
      $(this).find("button").removeClass("active");
    } else {
      $(".set > a i#plus").removeClass("fa-minus")
        .addClass("fa-plus");
      $(this).find("i#plus").removeClass("fa-plus").addClass("fa-minus");
      $(".set > a").removeClass("active");
      $(this).addClass("active");
      $(".content").slideUp(200);
      $(this).siblings(".content").slideDown(200);
      $(".set > a button").removeClass("active");
      $(this).find("button").addClass("active");  
    }
  })
});
