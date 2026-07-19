import styles from "./Input.module.css";

type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export default function Input({ className, ...rest }: InputProps) {
  return <input className={[styles.input, className].filter(Boolean).join(" ")} {...rest} />;
}
