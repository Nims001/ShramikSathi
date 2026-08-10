import Image from "next/image";

export default function Logo({ className }: { className?: string }) {
  return (
    <Image
      src="/logo.png"
      alt="ShramikSathi logo"
      width={502}
      height={512}
      className={`h-full w-full rounded-full object-cover ${className ?? ""}`}
    />
  );
}
