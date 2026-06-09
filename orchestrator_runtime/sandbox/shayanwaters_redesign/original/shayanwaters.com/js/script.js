wow = new WOW({
        offset: 50,  
    }).init();

// Прелоадер
window.onload=function(){   
  setTimeout(function(){
    $(".preloader").slideUp(); // Прелоадер
    
  
  }, 500);
  
  //  Удаление рекламы хостинга (*можно удалить)
  $('[rel="nofollow"]').parent().hide();
  $('.cbalink').hide();
}


$(document).ready(function(){


    // ================= Работа уведомления о cookies ================= 

    // функция возвращает cookie с именем name, если есть, если нет, то undefined    
    function getCookie(name) {
        let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
        ));
        return matches ? decodeURIComponent(matches[1]) : undefined;
    }
    let cookiecook = getCookie("cookiecook"), cookiewin = $('.cookies');    

    // проверяем, есть ли у нас cookie, с которой мы не показываем окно и если нет, запускаем показ
    if (cookiecook != "no") {
        // показываем
        setTimeout(function(){
            cookiewin.addClass("active");
        }, 1000);  

        // закрываем по клику
        $(".cookies__button").click(function() {
            cookiewin.removeClass("active");    
            // записываем cookie на 1 день, с которой мы не показываем окно
            let date = new Date;
            date.setDate(date.getDate() + 1);    
            document.cookie = "cookiecook=no; path=/; expires=" + date.toUTCString();               
        });
    }

    //E-mail Ajax Send
	$("form").submit(function() { //Change
		var th = $(this);
		$.ajax({
			type: "POST",
			url: "mail.php", //Change
			data: th.serialize()
		}).done(function() {
			alert("Дякуємо!");
			setTimeout(function() {
				// Done Functions
				th.trigger("reset");
			}, 1000);
		});
		return false;
	});


    // ================= Работа Мобильного меню ================= 
    $(".nav-mobile__toggle").click(function (){
       $(this).toggleClass("active"); 
       $("body").toggleClass("overflow-hidden");
       $(".nav-mobile__menu").slideToggle();
       return false;
    });

    $(".nav-mobile__menu li > ul").each(function (){
        $(this).parent().addClass("has-child");
    });

    $(".nav-mobile__menu li.has-child > a").each(function (){
      $(this).before(`<div class="nav-mobile__item"></div>`);;
      $(this).parent().find(".nav-mobile__item").append(this);
    });

    $(".nav-mobile__item").click(function (){
        $(this).toggleClass("active");
        $(this).parent().find("> ul").slideToggle();
    });

    // Работа табов 
    $(".product-tabs__nav").on("click", "li:not(.active)", function() {
        $(this).addClass("active").siblings().removeClass("active");   
        $(".product-tabs__content").find(".product-tabs__tab").removeClass("active").eq($(this).index()).addClass("active");
    });
});










