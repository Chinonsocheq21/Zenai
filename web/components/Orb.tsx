export default function Orb({ size = 40 }: { size?: number }) {
  return <span aria-hidden className="orb inline-block shrink-0" style={{ width: size, height: size }} />;
}
