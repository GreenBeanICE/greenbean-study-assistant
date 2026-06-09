import { useRef, useCallback, useEffect, type MouseEvent } from "react";

/** 可拖拽调整宽度的分隔条 */
function ResizableHandle({
  onResize,
  position = "left",
}: {
  onResize: (delta: number) => void;
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
    },
    [],
  );

  useEffect(() => {
    const handleMouseMove = (e: globalThis.MouseEvent) => {
      if (!draggingRef.current) return;
      const delta = e.clientX - startXRef.current;
      startXRef.current = e.clientX;
      onResize(delta);
    };

    const handleMouseUp = () => {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [onResize]);

  return (
    <div
      ref={handleRef}
      onMouseDown={handleMouseDown}
      className="w-1.5 flex-shrink-0 cursor-col-resize hover:bg-blue-500/20 dark:hover:bg-blue-400/20 active:bg-blue-500/40 dark:active:bg-blue-400/40 transition-colors duration-150 relative group"
    >
      <div className="absolute inset-y-0 -left-1 -right-1" />
    </div>
  );
}

export default ResizableHandle;