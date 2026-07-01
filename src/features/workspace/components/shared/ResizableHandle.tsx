import { useRef, useCallback, useEffect, type MouseEvent } from "react";

/** 可拖拽调整宽度的分隔条 */
function ResizableHandle({
  onResize,
  onDoubleClick,
  onDragStateChange,
  position = "left",
}: {
  onResize: (delta: number, clientX?: number) => void;
  onDoubleClick?: () => void;
  onDragStateChange?: (isDragging: boolean) => void;
  position?: "left" | "right";
}) {
  const handleRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);
  const startXRef = useRef(0);

  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      e.preventDefault();
      draggingRef.current = true;
      startXRef.current = e.clientX;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      onDragStateChange?.(true);
    },
    [onDragStateChange],
  );

  useEffect(() => {
    const handleMouseMove = (e: globalThis.MouseEvent) => {
      if (!draggingRef.current) return;
      const delta = e.clientX - startXRef.current;
      startXRef.current = e.clientX;
      onResize(delta, e.clientX);
    };

    const handleMouseUp = () => {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      onDragStateChange?.(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [onResize, onDragStateChange]);

  return (
    <div
      ref={handleRef}
      onMouseDown={handleMouseDown}
      onDoubleClick={onDoubleClick}
      aria-label={position === "left" ? "调整左侧面板宽度" : "调整右侧面板宽度"}
      className="w-1 flex-shrink-0 cursor-col-resize hover:bg-blue-500/20 active:bg-blue-500/40 transition-colors duration-150"
    />
  );
}

export default ResizableHandle;
