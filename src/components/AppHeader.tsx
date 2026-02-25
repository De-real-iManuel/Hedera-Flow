import logo from "@/assets/hedera-flow-logo.png";

const AppHeader = ({ title }: { title?: string }) => {
  return (
    <header className="flex items-center justify-between px-5 pt-3 pb-2">
      <div className="flex items-center gap-2.5">
        <img src={logo} alt="Hedera Flow" className="w-8 h-8 rounded-lg" />
        <span className="text-lg font-bold tracking-tight text-foreground">
          {title || "Hedera Flow"}
        </span>
      </div>
      <div className="w-9 h-9 rounded-full gradient-navy flex items-center justify-center">
        <span className="text-sm font-semibold text-primary-foreground">E</span>
      </div>
    </header>
  );
};

export default AppHeader;
