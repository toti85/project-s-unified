
jQuery(function($){

	// Создание Overlay
	$(".u-mobile-menu").after('<div class="u-menu-overlay"></div>')
	
	// Добавление классов  
	$("ul.u-nav-group").each(function (){
		$(this).addClass("u-nav");
		$(this).find("ul").addClass("u-nav");
	});

	// Создание структуры подменю
	$("ul.u-nav-group ul").each(function (){
		$(this).before(`<div class="u-nav-wrapper"><div class="u-nav-content"></div></div>`);
		var container = $(this).prev().find(".u-nav-content");
		var content = $(this);
		container.append(content);
	});

	// Добавление контента в подменю
	$(".u-nav-content").each(function (){
		$(this).prepend(`<h2 class="u-nav__title"></h2><a href="#" class="u-nav__back">Назад <i class="fas fa-angle-left"></i></a>`);
	});

	// Добавление классов  
	$("ul.u-nav").each(function (){
		$(this).find("li").addClass("u-nav__item");
		$(this).find("a").addClass("u-nav__link");
	});

	// Добавление иконки всем елементам в которых есть подменю
	$(".u-nav__item").each(function (){
		$(this).has(".u-nav-wrapper").find("> a").append(`<span class="u-nav__next fas fa-angle-right"></span>`);
	});

	// Добавление заголовка подменю от родителя
	$(".u-nav__item").each(function (){
		var str =	$(this).has(".u-nav-wrapper").find("> .u-nav__link > span").text();
		$(this).has(".u-nav-wrapper").find("> .u-nav-wrapper > .u-nav-content > .u-nav__title").html(str);
	});  

	// Создание группы
	$(".u-nav[u-nav-group]").each(function (){
		var group_name =$(this).attr("u-nav-group");
		$(this).prepend('<li class="u-nav__item-title">' + group_name + '</li>')
	});

	
	// Переменна для анимации смещения
	var transform = 0;

	// ========== Открыть / Закрыть Меню ========== 
	$(".u-mobile-menu-switcher, .u-menu-overlay, .u-mobile-menu__close").click(function (){
		$("body").toggleClass("u-mobile-menu-open");
	});


	// ========== Открыть подменю ========== 
	$(".u-nav__next").on("click", function(){
		
		var item = $(this).parent().parent();

		// Активировать подменю
		item.find("> .u-nav-wrapper").addClass("active");

		// Анимация смещения 
		transform = transform + 40;
		$(".u-mobile-menu__wrapper").css("transform", "translate3d(" + transform + "px , 0, 0)");
		item.find("> .u-nav-wrapper").css("transform", "translate3d(-" + 40 + "px , 0, 0)");
		
		// Добавление Overlay
		$(".u-mobile-menu__wrapper").addClass("open");
		item.find("> .u-nav-wrapper").parents(".u-nav-wrapper").addClass("open");	

		return false;
	});



	// ========== Закрыть подменю ==========
	$(".u-nav__back").on("click", function (){

		var item = $(this).parent().parent();
		
		// Закрыть подменю 
		item.removeClass("active");	

		// Анимация смещения 
		transform = transform - 40;
		$(".u-mobile-menu__wrapper").css("transform", "translate3d(" + transform + "px , 0, 0)");
		item.css("transform", "translate3d(-" + 100 + "% , 0, 0)");

		// Удалить Overlay
		item.parent().parent().parent().parent().removeClass("open");

		if($(".u-nav-wrapper.active").length == 0){		
			$(".u-mobile-menu__wrapper").removeClass("open");
		}	
	});


	// При клике вне подменю закрыть текущее подменю
	$(document).mouseup(function (e){
		$(".u-nav-wrapper.active").each(function() {
			if(!$(this).hasClass("open")){
				if (!$(this).is(e.target) && $(this).has(e.target).length === 0){
					$(this).removeClass("active");
					$(this).parent().parent().parent().parent().removeClass("open");
					$(this).css("transform", "translate3d(-" + 100 + "% , 0, 0)");
					transform = transform - 40;
					$(".u-mobile-menu__wrapper").css("transform", "translate3d(" + transform + "px , 0, 0)");	
				}		
			}
		});
	});


	// Закрыть 
	$(".u-menu-overlay").click(function (){
		$(".u-nav-wrapper").removeClass("active");
		$(".u-nav-wrapper").removeClass("open");
		$(".u-nav-wrapper").css("transform", "translate3d(-100%, 0, 0)");
		transform = 0; 
		$(".u-mobile-menu__wrapper").removeClass("open");
		$(".u-mobile-menu__wrapper").css("transform", "translate3d(" + transform + "px , 0, 0)");	
	});

});