//navbar 

const burgerMenu = document.querySelector('.burger-menu');
const menuItems = document.querySelector('.menu-items');

burgerMenu.addEventListener('click', () => {
  menuItems.classList.toggle('active');
});


// animate on scroll // wow et animate
$(function(){
  new WOW().init();
})