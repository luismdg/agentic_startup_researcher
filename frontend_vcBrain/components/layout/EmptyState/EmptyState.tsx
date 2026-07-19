import Icon, { type IconName } from "@/components/ui/Icon/Icon";
import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  icon?: IconName;
  title: string;
  description?: string;
}

export default function EmptyState({ icon = "tray", title, description }: EmptyStateProps) {
  return (
    <div className={styles.wrapper}>
      <span className={styles.icon}>
        <Icon name={icon} size={28} />
      </span>
      <p className={styles.title}>{title}</p>
      {description && <p className={styles.description}>{description}</p>}
    </div>
  );
}
