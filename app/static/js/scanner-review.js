document.querySelectorAll('[data-scan-magnifier]').forEach((surface) => {
  const card = surface.querySelector('.scan-review-card');
  const lens = surface.querySelector('[data-scan-lens]');
  const status = surface.closest('[data-scan-review]').querySelector('[data-scan-magnifier-status]');
  const source = new Image();
  const zoom = 3;
  let point = { x: .5, y: .5 };
  let active = false;
  let frame = null;

  const hide = () => {
    active = false;
    lens.hidden = true;
  };

  const draw = () => {
    frame = null;
    if (!active || !source.complete || !source.naturalWidth) return;
    const bounds = card.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    const size = Math.min(220, bounds.width, bounds.height);
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const pixels = Math.round(size * ratio);
    if (lens.width !== pixels || lens.height !== pixels) {
      lens.width = pixels;
      lens.height = pixels;
    }
    lens.style.width = `${size}px`;
    lens.style.height = `${size}px`;
    lens.style.left = `${Math.max(0, Math.min(bounds.width - size, point.x * bounds.width - size / 2))}px`;
    lens.style.top = `${Math.max(0, Math.min(bounds.height - size, point.y * bounds.height - size / 2))}px`;
    const context = lens.getContext('2d');
    const scale = bounds.width / source.naturalWidth * zoom * ratio;
    context.fillStyle = '#fff';
    context.fillRect(0, 0, pixels, pixels);
    context.drawImage(source,
      pixels / 2 - point.x * source.naturalWidth * scale,
      pixels / 2 - point.y * source.naturalHeight * scale,
      source.naturalWidth * scale, source.naturalHeight * scale);
    lens.hidden = false;
  };

  const scheduleDraw = () => {
    if (frame === null) frame = requestAnimationFrame(draw);
  };

  const followPointer = (event) => {
    const bounds = card.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    point = {
      x: Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)),
      y: Math.max(0, Math.min(1, (event.clientY - bounds.top) / bounds.height)),
    };
    active = true;
    scheduleDraw();
  };

  surface.addEventListener('pointerenter', (event) => {
    if (event.pointerType !== 'touch') followPointer(event);
  });
  surface.addEventListener('pointermove', followPointer);
  surface.addEventListener('pointerdown', (event) => {
    surface.focus({ preventScroll: true });
    followPointer(event);
  });
  surface.addEventListener('pointerleave', (event) => {
    if (event.pointerType !== 'touch') hide();
  });
  surface.addEventListener('pointercancel', hide);
  surface.addEventListener('focus', () => {
    active = true;
    scheduleDraw();
  });
  surface.addEventListener('blur', hide);
  surface.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      hide();
      return;
    }
    const moves = { ArrowLeft: [-.03, 0], ArrowRight: [.03, 0], ArrowUp: [0, -.03], ArrowDown: [0, .03] };
    const move = moves[event.key];
    if (!move && event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    if (move) {
      point.x = Math.max(0, Math.min(1, point.x + move[0]));
      point.y = Math.max(0, Math.min(1, point.y + move[1]));
      active = true;
    } else {
      active = !active;
    }
    if (active) scheduleDraw();
    else hide();
  });
  document.addEventListener('pointerdown', (event) => {
    if (!surface.contains(event.target)) hide();
  });
  source.addEventListener('load', scheduleDraw);
  source.addEventListener('error', () => {
    hide();
    status.textContent = 'A lupa não carregou. Use “Abrir imagem completa” para conferir o cartão.';
  });
  new ResizeObserver(scheduleDraw).observe(card);
  source.src = card.dataset.alignedSrc;
});
