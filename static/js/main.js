/*
  Небольшое поведение страницы INVP01.
  Библиотек нет: только обычный JavaScript в браузере.
  Если скрипт не загрузится, материалы и форма всё равно работают.
*/

document.addEventListener("DOMContentLoaded", function () {
  setupFilters();
  setupFlashClose();
  setupReadingProgress();
  setupStickyCta();
});

// Кнопки «Основы», «Практика» и другие прячут лишние карточки.
function setupFilters() {
  var chips = document.querySelectorAll(".chip");
  var cards = document.querySelectorAll(".card");
  var status = document.getElementById("filter-status");
  var empty = document.querySelector(".cards-empty");

  if (!chips.length || !cards.length) {
    return;
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var tag = chip.dataset.tag;

      chips.forEach(function (item) {
        var active = item === chip;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", active ? "true" : "false");
      });

      var visible = 0;
      cards.forEach(function (card) {
        var show = tag === "all" || card.dataset.tag === tag;
        card.classList.toggle("is-hidden", !show);
        if (show) {
          visible += 1;
        }
      });

      if (status) {
        status.textContent = "Показано: " + visible;
      }
      if (empty) {
        empty.hidden = visible !== 0;
      }
    });
  });
}

// Крестик у зелёного или красного сообщения после отправки формы.
function setupFlashClose() {
  document.querySelectorAll(".flash-close").forEach(function (button) {
    button.addEventListener("click", function () {
      var flash = button.closest(".flash");
      if (flash) {
        flash.remove();
      }
    });
  });
}

// Тонкая полоска сверху на странице материала: сколько уже прочитано.
function setupReadingProgress() {
  var bar = document.getElementById("progress-bar");
  if (!bar) {
    return;
  }

  function update() {
    var root = document.documentElement;
    var scrollable = root.scrollHeight - root.clientHeight;
    var progress = scrollable > 0 ? root.scrollTop / scrollable : 0;
    bar.style.transform = "scaleX(" + progress + ")";
  }

  update();
  window.addEventListener("scroll", update, { passive: true });
}

// На телефоне нижняя кнопка ведёт к форме и прячется, когда форма уже видна.
function setupStickyCta() {
  var sticky = document.querySelector(".sticky-cta");
  var subscribe = document.getElementById("subscribe");
  if (!sticky) {
    return;
  }

  function onScroll() {
    sticky.classList.toggle("is-visible", window.scrollY > 520);
  }

  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  if (!subscribe || !("IntersectionObserver" in window)) {
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        sticky.classList.toggle("is-hidden-by-target", entry.isIntersecting);
      });
    },
    { threshold: 0.35 }
  );
  observer.observe(subscribe);
}
